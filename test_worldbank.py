import requests
import pandas as pd


BASE_URL = "https://api.worldbank.org/v2"


INDICATORS = {
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "expense_pct_gdp": "GC.XPN.TOTL.GD.ZS",
    "revenue_pct_gdp": "GC.REV.XGRT.GD.ZS",
    "exports_pct_gdp": "NE.EXP.GNFS.ZS",
    "inflation": "FP.CPI.TOTL.ZG",
}


def fetch_indicator(countries, indicator_code, start_year=2015, end_year=2024):
    countries_string = ";".join(countries)

    url = (
        f"{BASE_URL}/country/"
        f"{countries_string}/indicator/{indicator_code}"
    )

    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 1000
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    if not data or len(data) < 2 or data[1] is None:
        return pd.DataFrame()

    rows = []

    for item in data[1]:
        rows.append({
            "country": item["country"]["value"],
            "country_code": item["countryiso3code"],
            "year": int(item["date"]),
            "indicator": item["indicator"]["id"],
            "indicator_name": item["indicator"]["value"],
            "value": item["value"]
        })

    return pd.DataFrame(rows)


countries = ["USA", "CHN", "DNK"]

all_data = []

for name, indicator_code in INDICATORS.items():

    print(f"Fetching {name}...")

    df = fetch_indicator(
        countries,
        indicator_code,
        start_year=2015,
        end_year=2024
    )

    df["variable"] = name

    all_data.append(df)


data = pd.concat(all_data, ignore_index=True)

print("\nFirst rows:")
print(data.head(20))

print("\nShape:")
print(data.shape)

print("\nAvailable indicators:")
print(data["variable"].unique())