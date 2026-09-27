# World Bank Hackathon: Financial Inclusion

1.4 billion people have financial invisibility. These people are unable to get loans, mortgages, or other financial resources because of being unbanked. We wish to find some indicators for financial invisibility to raise awareness about the topic.

## Data pipeline

The pipeline in `scripts/fetch_worldbank.py` retrieves World Bank data for 2011–2024 and keeps the five Global Findex survey years: 2011, 2014, 2017, 2021, and 2024.

It excludes World Bank aggregate entities, attaches each country’s current income group and region, preserves API responses in `data/raw`, and generates analysis ready files in `data/processed`.

### Main indicators

The dataset includes:

- Account ownership for the total adult population
- Account ownership by gender, age, education, and income group
- Internet use and mobile subscriptions
- ATM and commercial bank branch density
- GDP per capita, GDP growth, and inflation
- Unemployment and labor force participation
- Urban population, adult literacy, and income inequality
- Population

### Processed outputs

| File | Purpose |
| --- | --- |
| `data/processed/worldbank_indicator_observations.csv` | Long format observations with one country, year, and indicator per row |
| `data/processed/worldbank_country_year.csv` | Wide country year table with one indicator per column |
| `data/processed/findex_years.csv` | Country level data restricted to Global Findex survey years |
| `data/processed/missingness_report.csv` | Availability and missingness summary for each indicator |
| `data/processed/dashboard_data.json` | Findex year records prepared for dashboard use |

Rebuild the processed data with:

```powershell
python scripts/fetch_worldbank.py
```
This command requires an internet connection because it calls the World Bank API.

## Cluster analysis

The cluster analysis groups countries by the environment surrounding financial access. It does not use account ownership, the unbanked rate, the gender gap, or the income gap as clustering inputs. Those outcomes are attached afterward so that the groups are not defined by the result being studied.

The model uses eight features from 2024:

1. Internet users
2. Mobile subscriptions
3. GDP per capita
4. Unemployment
5. Labor force participation
6. Urban population
7. ATM density
8. Commercial bank branch density

GDP per capita, ATM density, and bank branch density receive a `log1p` transformation. Missing feature values are filled with the median, and all features are standardized with z-scores. A country must have account ownership data and at least six of the eight clustering features to be included.

The script evaluates K-means solutions from two through six clusters and selects the number of clusters with the highest silhouette score. The current 2024 analysis selects two clusters across 133 eligible countries:

- **Cluster 1:** stronger average digital access, income, urbanization, and financial infrastructure
- **Cluster 2:** more constrained average digital access and financial infrastructure

Cluster labels describe patterns in the input data. They are not country rankings and do not establish causation.

Run the analysis with:

```powershell
python scripts/cluster_countries.py
```

This creates:

| File | Purpose |
| --- | --- |
| `data/analysis/cluster_assignments.csv` | Country level cluster assignments, PCA coordinates, and analysis fields |
| `data/analysis/cluster_profiles.csv` | Cluster averages and standardized feature profiles |
| `data/analysis/cluster_diagnostics.csv` | Inertia and silhouette scores for each tested cluster count |
| `data/analysis/cluster_dashboard.json` | Combined dashboard payload used by the Flask API and Vue frontend |

`data/analysis/cluster_dashboard.json` is the authoritative dashboard file. The similarly named file in the repository root is a duplicate from an earlier prototype and is not read by the current dashboard endpoint.

## Dashboard

The interactive desktop dashboard includes:

- Choropleth maps for the unbanked rate, gender account gap, and income account gap
- Country details for account access, digital access, economic context, and financial infrastructure
- A clear no data state for countries without enough observations
- A PCA scatter plot showing similarity across the eight clustering features
- A cluster profile heatmap showing standardized feature averages
- Linked country selection between the analysis view and country detail panel

The frontend uses Vue 3, TypeScript, Vite, Axios, and Syncfusion Maps. The backend uses Flask and serves the dashboard data at `/api/cluster-dashboard`.

## Local setup

### Requirements

- Python 3.9 or newer
- Node.js 22.18 or newer, or Node.js 24.12 or newer

Install the Python dependencies from the repository root:

```powershell
python -m pip install flask flask-cors numpy pandas requests
```

Install the frontend dependencies:

```powershell
cd wb-frontend
npm install
cd ..
```

### Run locally

The backend and frontend must run in separate terminals.

Terminal 1 — start the Flask API:

```powershell
python app.py
```

Terminal 2 — start the Vue development server:

```powershell
cd wb-frontend
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in a desktop browser. The Flask API runs on [http://127.0.0.1:5001](http://127.0.0.1:5001), and Vite proxies frontend `/api` requests to it.

Build and type check the frontend with:

```powershell
cd wb-frontend
npm run build
```

## Project structure

```text
worldbank-hackathon/
├── app.py                         # Flask API
├── scripts/
│   ├── fetch_worldbank.py         # Data collection and processing
│   └── cluster_countries.py       # K-means, diagnostics, and PCA
├── data/
│   ├── raw/                       # Original API responses
│   ├── processed/                 # Analysis ready country data
│   └── analysis/                  # Cluster outputs for the dashboard
└── wb-frontend/                   # Vue and TypeScript frontend
```

## Data sources and licensing

Data were retrieved through the World Bank Indicators API and include indicators from World Bank Open Data, the Global Findex Database, and the IMF Financial Access Survey.

World Bank produced open datasets are generally distributed under the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/), subject to the [World Bank Data Access and Licensing terms](https://datacatalog.worldbank.org/public-licenses) and any dataset specific terms.

Suggested attribution:

> Source: World Bank Open Data, Global Findex Database, and World Development Indicators, accessed through the World Bank Indicators API. Data were processed and transformed by the project authors.

Some indicators, including ATM and commercial bank branch density, originate from the IMF Financial Access Survey and may be subject to source specific terms.

This project is independent and is not endorsed by or affiliated with the World Bank Group or the International Monetary Fund. World Bank and IMF names and logos must not be used to imply endorsement.

Third party software remains subject to its respective licenses. No license has yet been specified for the original source code in this repository.
