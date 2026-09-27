"""Cluster countries by their 2024 financial-access environment.

Account ownership and subgroup gaps are kept out of the clustering features.
They are attached afterward so the clusters can be compared against the
financial-inclusion outcomes the project is trying to understand.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


YEAR = 2024
RANDOM_SEED = 42
K_VALUES = range(2, 7)
N_INIT = 40
MAX_ITERATIONS = 300
MIN_OBSERVED_FEATURES = 6

FEATURES = [
    "internet_users",
    "mobile_subscriptions",
    "gdp_per_capita",
    "unemployment",
    "labor_force_participation",
    "urban_population",
    "atm_density",
    "bank_branch_density",
]

MODEL_FEATURES = [
    "internet_users",
    "mobile_subscriptions",
    "log_gdp_per_capita",
    "unemployment",
    "labor_force_participation",
    "urban_population",
    "log_atm_density",
    "log_bank_branch_density",
]

# Positive values mean that a larger standardized feature contributes to a
# stronger financial-access environment. Unemployment points the other way.
ACCESS_DIRECTION = np.array([1, 1, 1, -1, 1, 1, 1, 1], dtype=float)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "findex_years.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"


def pairwise_distances(values):
    """Return Euclidean distances between every pair of observations."""
    differences = values[:, None, :] - values[None, :, :]
    return np.sqrt(np.sum(differences * differences, axis=2))


def silhouette_score(values, labels):
    """Compute the mean silhouette coefficient without external libraries."""
    distances = pairwise_distances(values)
    unique_labels = np.unique(labels)
    scores = []

    for row_index, label in enumerate(labels):
        same_cluster = labels == label
        same_cluster[row_index] = False

        if not same_cluster.any():
            scores.append(0.0)
            continue

        within_distance = distances[row_index, same_cluster].mean()
        nearest_other_distance = min(
            distances[row_index, labels == other_label].mean()
            for other_label in unique_labels
            if other_label != label
        )
        denominator = max(within_distance, nearest_other_distance)
        score = (
            (nearest_other_distance - within_distance) / denominator
            if denominator
            else 0.0
        )
        scores.append(score)

    return float(np.mean(scores))


def run_kmeans(values, cluster_count):
    """Run deterministic multi-start K-means and keep the lowest-inertia fit."""
    random = np.random.default_rng(RANDOM_SEED + cluster_count)
    best_result = None

    for _ in range(N_INIT):
        initial_rows = random.choice(len(values), size=cluster_count, replace=False)
        centers = values[initial_rows].copy()
        labels = np.full(len(values), -1, dtype=int)

        for _ in range(MAX_ITERATIONS):
            squared_distances = np.sum(
                (values[:, None, :] - centers[None, :, :]) ** 2,
                axis=2,
            )
            new_labels = np.argmin(squared_distances, axis=1)

            if np.array_equal(new_labels, labels):
                break
            labels = new_labels

            new_centers = []
            nearest_distance = squared_distances.min(axis=1)
            for cluster_id in range(cluster_count):
                members = values[labels == cluster_id]
                if len(members):
                    new_centers.append(members.mean(axis=0))
                else:
                    farthest_row = int(np.argmax(nearest_distance))
                    new_centers.append(values[farthest_row])
            centers = np.vstack(new_centers)

        final_squared_distances = np.sum(
            (values[:, None, :] - centers[None, :, :]) ** 2,
            axis=2,
        )
        labels = np.argmin(final_squared_distances, axis=1)
        inertia = float(
            final_squared_distances[np.arange(len(values)), labels].sum()
        )

        if best_result is None or inertia < best_result["inertia"]:
            best_result = {
                "labels": labels.copy(),
                "centers": centers.copy(),
                "inertia": inertia,
            }

    return best_result


def principal_components(values):
    """Project standardized observations onto two principal components."""
    centered = values - values.mean(axis=0)
    _, singular_values, components = np.linalg.svd(centered, full_matrices=False)
    coordinates = centered @ components[:2].T
    variances = singular_values**2
    explained_ratio = variances / variances.sum()
    return coordinates, explained_ratio[:2]


def dataframe_records(frame):
    """Convert a DataFrame to JSON-safe records with null instead of NaN."""
    return json.loads(frame.to_json(orient="records", force_ascii=False))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(INPUT_PATH)
    required_columns = {
        "country",
        "iso3",
        "year",
        "region_code",
        "region",
        "current_income_group_code",
        "current_income_group",
        "account_ownership",
        "account_female",
        "account_male",
        "account_poorest40",
        "account_richest60",
        *FEATURES,
    }
    missing_columns = sorted(required_columns.difference(data.columns))
    if missing_columns:
        raise ValueError(
            "Required columns are missing from findex_years.csv: "
            + ", ".join(missing_columns)
        )

    year_data = data[data["year"] == YEAR].copy().reset_index(drop=True)
    if year_data.empty:
        raise ValueError(f"No records are available for {YEAR}.")

    year_data["unbanked_rate"] = 100 - year_data["account_ownership"]
    year_data["gender_account_gap"] = (
        year_data["account_male"] - year_data["account_female"]
    )
    year_data["income_account_gap"] = (
        year_data["account_richest60"] - year_data["account_poorest40"]
    )
    year_data["observed_feature_count"] = year_data[FEATURES].notna().sum(axis=1)
    year_data["imputed_feature_count"] = (
        len(FEATURES) - year_data["observed_feature_count"]
    )

    eligible_mask = (
        year_data["account_ownership"].notna()
        & (year_data["observed_feature_count"] >= MIN_OBSERVED_FEATURES)
    )
    eligible = year_data.loc[eligible_mask].copy()
    if len(eligible) <= max(K_VALUES):
        raise ValueError("Too few eligible countries to run the requested clusters.")

    model_data = eligible[FEATURES].astype(float).copy()
    for skewed_column in [
        "gdp_per_capita",
        "atm_density",
        "bank_branch_density",
    ]:
        model_data[skewed_column] = np.log1p(
            model_data[skewed_column].clip(lower=0)
        )
    model_data.columns = MODEL_FEATURES

    medians = model_data.median()
    imputed = model_data.fillna(medians)
    means = imputed.mean()
    standard_deviations = imputed.std(ddof=0).replace(0, 1)
    standardized = (imputed - means) / standard_deviations
    values = standardized.to_numpy(dtype=float)

    diagnostics = []
    fitted_models = {}
    for cluster_count in K_VALUES:
        result = run_kmeans(values, cluster_count)
        result["silhouette_score"] = silhouette_score(values, result["labels"])
        fitted_models[cluster_count] = result
        diagnostics.append(
            {
                "cluster_count": cluster_count,
                "inertia": result["inertia"],
                "silhouette_score": result["silhouette_score"],
            }
        )

    selected_cluster_count = max(
        diagnostics,
        key=lambda row: (row["silhouette_score"], -row["cluster_count"]),
    )["cluster_count"]
    selected = fitted_models[selected_cluster_count]

    # K-means numeric labels are arbitrary. Reorder them from higher to lower
    # composite access profile so colors and IDs remain interpretable.
    access_scores = selected["centers"] @ ACCESS_DIRECTION / len(ACCESS_DIRECTION)
    ordered_original_labels = np.argsort(-access_scores)
    stable_label_map = {
        int(original_label): stable_id
        for stable_id, original_label in enumerate(ordered_original_labels, start=1)
    }
    stable_labels = np.array(
        [stable_label_map[int(label)] for label in selected["labels"]], dtype=int
    )

    pca_coordinates, pca_explained_ratio = principal_components(values)

    year_data["cluster_id"] = pd.Series(pd.NA, index=year_data.index, dtype="Int64")
    year_data["cluster_key"] = pd.NA
    year_data["cluster_label"] = pd.NA
    year_data["pca_x"] = np.nan
    year_data["pca_y"] = np.nan
    year_data["cluster_status"] = "missing_account_ownership"
    year_data.loc[
        year_data["account_ownership"].notna() & ~eligible_mask,
        "cluster_status",
    ] = "insufficient_features"

    eligible_indexes = year_data.index[eligible_mask]
    year_data.loc[eligible_indexes, "cluster_id"] = stable_labels
    year_data.loc[eligible_indexes, "cluster_key"] = [
        f"cluster_{cluster_id}" for cluster_id in stable_labels
    ]
    year_data.loc[eligible_indexes, "cluster_label"] = [
        f"Cluster {cluster_id}" for cluster_id in stable_labels
    ]
    year_data.loc[eligible_indexes, "pca_x"] = pca_coordinates[:, 0]
    year_data.loc[eligible_indexes, "pca_y"] = pca_coordinates[:, 1]
    year_data.loc[eligible_indexes, "cluster_status"] = "assigned"

    assigned = year_data[year_data["cluster_status"] == "assigned"].copy()
    profile_rows = []
    stable_access_scores = {
        stable_label_map[int(original_label)]: float(access_scores[original_label])
        for original_label in ordered_original_labels
    }
    for cluster_id in range(1, selected_cluster_count + 1):
        members = assigned[assigned["cluster_id"] == cluster_id]
        standardized_members = standardized.loc[members.index]
        profile = {
            "cluster_id": cluster_id,
            "cluster_key": f"cluster_{cluster_id}",
            "cluster_label": f"Cluster {cluster_id}",
            "country_count": int(len(members)),
            "access_profile_score": stable_access_scores[cluster_id],
        }
        for column in FEATURES + [
            "account_ownership",
            "unbanked_rate",
            "gender_account_gap",
            "income_account_gap",
        ]:
            profile[f"mean_{column}"] = float(members[column].mean())
        for column in MODEL_FEATURES:
            profile[f"z_{column}"] = float(standardized_members[column].mean())
        profile_rows.append(profile)

    profiles = pd.DataFrame(profile_rows)
    diagnostics_frame = pd.DataFrame(diagnostics)
    diagnostics_frame["selected"] = (
        diagnostics_frame["cluster_count"] == selected_cluster_count
    )

    assignment_columns = [
        "country",
        "iso3",
        "year",
        "region_code",
        "region",
        "current_income_group_code",
        "current_income_group",
        "cluster_status",
        "cluster_id",
        "cluster_key",
        "cluster_label",
        "observed_feature_count",
        "imputed_feature_count",
        "pca_x",
        "pca_y",
        *FEATURES,
        "account_ownership",
        "unbanked_rate",
        "gender_account_gap",
        "income_account_gap",
    ]
    assignments = year_data[assignment_columns].sort_values("country")

    assignments.to_csv(OUTPUT_DIR / "cluster_assignments.csv", index=False)
    profiles.to_csv(OUTPUT_DIR / "cluster_profiles.csv", index=False)
    diagnostics_frame.to_csv(
        OUTPUT_DIR / "cluster_diagnostics.csv", index=False
    )

    dashboard = {
        "metadata": {
            "year": YEAR,
            "method": "K-means",
            "random_seed": RANDOM_SEED,
            "selected_cluster_count": selected_cluster_count,
            "selection_metric": "highest silhouette score",
            "features": MODEL_FEATURES,
            "transformation": {
                "gdp_per_capita": "log1p",
                "atm_density": "log1p",
                "bank_branch_density": "log1p",
                "all_features": "median imputation followed by z-score standardization",
            },
            "eligibility": {
                "account_ownership_required": True,
                "minimum_observed_features": MIN_OBSERVED_FEATURES,
                "eligible_countries": int(eligible_mask.sum()),
                "total_country_rows": int(len(year_data)),
            },
            "cluster_ordering": (
                "Cluster IDs are ordered from higher to lower composite "
                "financial-access environment; IDs are descriptive, not scores."
            ),
            "pca_explained_variance_ratio": {
                "pc1": float(pca_explained_ratio[0]),
                "pc2": float(pca_explained_ratio[1]),
            },
            "source_file": "data/processed/findex_years.csv",
        },
        "diagnostics": dataframe_records(diagnostics_frame),
        "profiles": dataframe_records(profiles),
        "countries": dataframe_records(assignments),
    }
    with (OUTPUT_DIR / "cluster_dashboard.json").open(
        "w", encoding="utf-8"
    ) as output_file:
        json.dump(dashboard, output_file, ensure_ascii=False, indent=2)

    print("Cluster analysis complete")
    print("-------------------------")
    print(f"Year: {YEAR}")
    print(f"Countries available for clustering: {int(eligible_mask.sum())}")
    print(f"Selected number of clusters: {selected_cluster_count}")
    print(
        "Selected silhouette score: "
        f"{selected['silhouette_score']:.3f}"
    )
    print("Cluster sizes:")
    for row in profiles.itertuples(index=False):
        print(f"  Cluster {row.cluster_id}: {row.country_count} countries")


if __name__ == "__main__":
    main()
