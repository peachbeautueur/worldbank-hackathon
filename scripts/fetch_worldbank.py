import json
from pathlib import Path

import pandas as pd
import requests


BASE_URL = "https://api.worldbank.org/v2"
START_YEAR = 2011
END_YEAR = 2024
FINDEX_YEARS = [2011, 2014, 2017, 2021, 2024]
REQUEST_TIMEOUT = 30

INDICATORS = {
    # Main dependent variable
    "account_ownership": "FX.OWN.TOTL.ZS",
    # Financial inclusion subgroup indicators
    "account_female": "FX.OWN.TOTL.FE.ZS",
    "account_male": "FX.OWN.TOTL.MA.ZS",
    "account_poorest40": "FX.OWN.TOTL.40.ZS",
    "account_richest60": "FX.OWN.TOTL.60.ZS",
    "account_young": "FX.OWN.TOTL.YG.ZS",
    "account_older": "FX.OWN.TOTL.OL.ZS",
    "account_primary_education": "FX.OWN.TOTL.PL.ZS",
    # Digital access
    "internet_users": "IT.NET.USER.ZS",
    "mobile_subscriptions": "IT.CEL.SETS.P2",
    # Physical financial access (sourced from the IMF Financial Access Survey)
    "atm_density": "FB.ATM.TOTL.P5",
    "bank_branch_density": "FB.CBK.BRCH.P5",
    # Economic conditions
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "inflation": "FP.CPI.TOTL.ZG",
    # Employment
    "unemployment": "SL.UEM.TOTL.ZS",
    "labor_force_participation": "SL.TLF.CACT.ZS",
    # Demographic context
    "urban_population": "SP.URB.TOTL.IN.ZS",
    "adult_literacy": "SE.ADT.LITR.ZS",
    "gini": "SI.POV.GINI",
    # Population
    "population": "SP.POP.TOTL",
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def request_json(url, params, description):
    """Request JSON from the World Bank API with retries and error handling."""
    for attempt in range(1, 3):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            if attempt == 1:
                print(f"WARNING: Timed out requesting {description}; retrying once.")
            else:
                print(f"WARNING: Timed out twice while requesting {description}.")
        except requests.RequestException as error:
            if attempt == 1:
                print(f"WARNING: HTTP error for {description}; retrying once: {error}")
            else:
                print(f"WARNING: HTTP error while requesting {description}: {error}")
        except ValueError as error:
            print(f"WARNING: Invalid JSON returned for {description}: {error}")
            return None
    return None


def save_raw_json(payload, path):
    """Save the API payload without flattening or changing its structure."""
    with path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, ensure_ascii=False, indent=2)


def api_records(payload, description):
    """Return observation records from a standard World Bank API response."""
    if not isinstance(payload, list) or not payload:
        print(f"WARNING: Empty or unexpected API response for {description}.")
        return []

    if len(payload) == 1 and isinstance(payload[0], dict) and "message" in payload[0]:
        print(f"WARNING: World Bank API message for {description}: {payload[0]['message']}")
        return []

    if len(payload) < 2 or payload[1] is None:
        print(f"WARNING: No observations returned for {description}.")
        return []

    if not isinstance(payload[1], list):
        print(f"WARNING: Unexpected observation format for {description}.")
        return []

    return payload[1]


def validate_indicator(indicator_name, indicator_code):
    """Check that an indicator code exists before requesting its observations."""
    payload = request_json(
        f"{BASE_URL}/indicator/{indicator_code}",
        {"format": "json"},
        f"indicator metadata for {indicator_name} ({indicator_code})",
    )
    records = api_records(payload, f"indicator metadata for {indicator_name}")
    if not records:
        print(f"WARNING: Skipping invalid or unavailable indicator {indicator_name}.")
        return False
    return True


def fetch_country_metadata():
    """Fetch country metadata and identify real countries from their region."""
    payload = request_json(
        f"{BASE_URL}/country",
        {"format": "json", "per_page": 400},
        "country metadata",
    )
    if payload is None:
        raise RuntimeError("Country metadata is required to remove aggregate entities.")

    save_raw_json(payload, RAW_DIR / "country_metadata.json")
    records = api_records(payload, "country metadata")
    if not records:
        raise RuntimeError("Country metadata contained no usable country records.")

    real_countries = []
    for country in records:
        region = country.get("region") or {}
        region_id = str(region.get("id") or "").strip()
        region_name = str(region.get("value") or "").strip()
        income_level = country.get("incomeLevel") or {}
        income_group_code = str(income_level.get("id") or "").strip()
        income_group = str(income_level.get("value") or "").strip()
        iso3 = str(country.get("id") or "").strip()
        name = str(country.get("name") or "").strip()
        if (
            region_id
            and region_id != "NA"
            and region_name != "Aggregates"
            and iso3
            and name
        ):
            real_countries.append(
                {
                    "country": name,
                    "iso3": iso3,
                    "region_code": region_id,
                    "region": region_name,
                    "current_income_group_code": income_group_code,
                    "current_income_group": income_group,
                }
            )

    if not real_countries:
        raise RuntimeError("No real countries could be identified from the metadata.")

    return pd.DataFrame(real_countries).drop_duplicates(subset=["iso3"])


def fetch_indicator(indicator_name, indicator_code, real_iso3):
    """Fetch one indicator, save its raw response, and return long records."""
    payload = request_json(
        f"{BASE_URL}/country/all/indicator/{indicator_code}",
        {
            "format": "json",
            "date": f"{START_YEAR}:{END_YEAR}",
            "per_page": 20000,
        },
        f"{indicator_name} ({indicator_code})",
    )
    if payload is None:
        return []

    save_raw_json(payload, RAW_DIR / f"{indicator_name}.json")
    observations = api_records(payload, indicator_name)
    if not observations:
        return []

    rows = []
    for observation in observations:
        iso3 = str(observation.get("countryiso3code") or "").strip()
        if iso3 not in real_iso3:
            continue

        country_info = observation.get("country") or {}
        year_value = observation.get("date")
        try:
            year = int(year_value)
        except (TypeError, ValueError):
            print(
                f"WARNING: Ignoring invalid year {year_value!r} for "
                f"{indicator_name}, {iso3}."
            )
            continue

        rows.append(
            {
                "country": country_info.get("value"),
                "iso3": iso3,
                "year": year,
                "indicator": indicator_name,
                "indicator_code": indicator_code,
                "value": observation.get("value"),
            }
        )

    return rows


def make_complete_country_year_grid(countries):
    """Create every real-country/year combination so missing rows remain visible."""
    years = pd.DataFrame({"year": range(START_YEAR, END_YEAR + 1)})
    countries = countries.copy()
    countries["_join_key"] = 1
    years["_join_key"] = 1
    grid = countries.merge(years, on="_join_key").drop(columns="_join_key")
    return grid[
        [
            "country",
            "iso3",
            "year",
            "region_code",
            "region",
            "current_income_group_code",
            "current_income_group",
        ]
    ]


def create_processed_outputs(long_data, countries):
    """Create long, wide, Findex-year, missingness, and dashboard outputs."""
    long_columns = [
        "country",
        "iso3",
        "year",
        "indicator",
        "indicator_code",
        "value",
    ]
    long_data = long_data.reindex(columns=long_columns)
    long_data = long_data.sort_values(
        ["country", "year", "indicator"], ignore_index=True
    )
    long_data.to_csv(
        PROCESSED_DIR / "worldbank_indicator_observations.csv", index=False
    )

    if long_data.empty:
        pivoted = pd.DataFrame(columns=["country", "iso3", "year"])
    else:
        pivoted = (
            long_data.pivot_table(
                index=["country", "iso3", "year"],
                columns="indicator",
                values="value",
                aggfunc="first",
            )
            .reset_index()
            .rename_axis(columns=None)
        )

    grid = make_complete_country_year_grid(countries)
    value_columns = list(INDICATORS.keys())
    wide_data = grid.merge(pivoted, on=["country", "iso3", "year"], how="left")
    wide_data = wide_data.reindex(
        columns=[
            "country",
            "iso3",
            "year",
            "region_code",
            "region",
            "current_income_group_code",
            "current_income_group",
        ]
        + value_columns
    ).sort_values(["country", "year"], ignore_index=True)
    wide_data.to_csv(PROCESSED_DIR / "worldbank_country_year.csv", index=False)

    findex_data = wide_data[wide_data["year"].isin(FINDEX_YEARS)].copy()
    findex_data.to_csv(PROCESSED_DIR / "findex_years.csv", index=False)

    report_rows = []
    row_count = len(findex_data)
    for indicator_name in value_columns:
        non_null_count = int(findex_data[indicator_name].notna().sum())
        missing_count = int(row_count - non_null_count)
        missing_percentage = (
            round((missing_count / row_count) * 100, 2) if row_count else 0.0
        )
        report_rows.append(
            {
                "indicator": indicator_name,
                "non_null_count": non_null_count,
                "missing_count": missing_count,
                "missing_percentage": missing_percentage,
            }
        )

    missingness = pd.DataFrame(report_rows)
    missingness.to_csv(PROCESSED_DIR / "missingness_report.csv", index=False)

    dashboard_records = json.loads(
        findex_data.to_json(orient="records", force_ascii=False)
    )
    with (PROCESSED_DIR / "dashboard_data.json").open(
        "w", encoding="utf-8"
    ) as output_file:
        json.dump(dashboard_records, output_file, ensure_ascii=False, indent=2)

    return wide_data, findex_data, missingness


def validate_no_aggregates(*datasets):
    """Fail loudly if well-known aggregate entities reach processed outputs."""
    aggregate_names = {"World", "High income", "Low income"}
    for dataset in datasets:
        if dataset.empty or "country" not in dataset.columns:
            continue
        found = aggregate_names.intersection(set(dataset["country"].dropna()))
        if found:
            raise ValueError(
                "Aggregate entities found in processed data: " + ", ".join(sorted(found))
            )


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching World Bank country metadata...")
    countries = fetch_country_metadata()
    real_iso3 = set(countries["iso3"])

    print("\nValidating indicators...")
    valid_indicators = {}
    unavailable_indicators = []
    for indicator_name, indicator_code in INDICATORS.items():
        if validate_indicator(indicator_name, indicator_code):
            valid_indicators[indicator_name] = indicator_code
        else:
            unavailable_indicators.append(indicator_name)

    print("\nFetching indicator observations...")
    all_rows = []
    successful_indicators = []
    no_data_indicators = list(unavailable_indicators)
    for indicator_name, indicator_code in valid_indicators.items():
        print(f"  Fetching {indicator_name} ({indicator_code})...")
        rows = fetch_indicator(indicator_name, indicator_code, real_iso3)
        if rows:
            all_rows.extend(rows)
            successful_indicators.append(indicator_name)
        else:
            no_data_indicators.append(indicator_name)

    long_data = pd.DataFrame(all_rows)
    wide_data, findex_data, missingness = create_processed_outputs(
        long_data, countries
    )
    validate_no_aggregates(long_data, wide_data, findex_data)

    high_missingness = missingness[missingness["missing_percentage"] >= 50]

    print("\nPipeline summary")
    print("----------------")
    print(f"Number of real countries: {len(countries)}")
    print(f"Number of indicators successfully retrieved: {len(successful_indicators)}")
    print(f"Number of indicators with no data: {len(no_data_indicators)}")
    if no_data_indicators:
        print("Indicators with no data: " + ", ".join(no_data_indicators))
    print(
        "Number of rows in worldbank_indicator_observations.csv: "
        f"{len(long_data)}"
    )
    print(f"Number of rows in worldbank_country_year.csv: {len(wide_data)}")
    print(f"Number of rows in findex_years.csv: {len(findex_data)}")
    print("Verified that World, High income, and Low income are absent.")

    if high_missingness.empty:
        print("No indicators have 50% or greater missingness in Findex years.")
    else:
        print("\nIndicators with 50% or greater missingness in Findex years:")
        for row in high_missingness.itertuples(index=False):
            print(f"  {row.indicator}: {row.missing_percentage:.2f}%")


if __name__ == "__main__":
    main()
