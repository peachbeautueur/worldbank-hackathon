from pathlib import Path

import pandas as pd
import requests

class Global:
    def __init__(self): 
        self.non_null_data_percentage = 100

    def extract_data(self, indicator_code):
        url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
        params = {"date": "2000:2026", "format": "json", "per_page": 5000}
        all_records = []
        total_pages = 1
        expected_records = 0
        page = 1
        ##csvName = "inputGovernmentHealthCareSpendPerCapita.csv"
        csvName = "outputGDPPerCapitaPPP.csv"
        with requests.Session() as session:
            while page <= total_pages:
                response = session.get(url, params={**params, "page": page}, timeout=30)
                response.raise_for_status()
                payload = response.json()

                if not isinstance(payload, list) or not payload:
                    raise ValueError(f"Unexpected World Bank API response on page {page}")
                if len(payload) == 1 and "message" in payload[0]:
                    raise ValueError(f"World Bank API error: {payload[0]['message']}")

                metadata, records = payload
                if page == 1:
                    total_pages = int(metadata["pages"])
                    expected_records = int(metadata["total"])
                if records is not None:
                    if not isinstance(records, list):
                        raise ValueError(f"Unexpected records format on page {page}")
                    all_records.extend(records)
                page += 1

        if len(all_records) != expected_records:
            raise ValueError(
                f"Fetched {len(all_records)} records, but the World Bank API reported "
                f"{expected_records}"
            )

        data = pd.json_normalize(all_records)
        csv_path = Path(__file__).with_name(csvName)
        data.to_csv(csv_path, index=False)
        print(
            f"Saved all {len(data)} rows from {total_pages} page(s) "
            f"to {csv_path}"
        )
        data
        if "value" not in data.columns:
            raise KeyError("Column 'value' not found in DataFrame.")
        return data

    def get_non_null_data_percentage(self):
        data = self.extract_data("NY.GDP.PCAP.PP.CD")
        total_count = len(data)
        non_null_count = data["value"].notnull().sum()
        percentage_non_null = (
            (non_null_count / total_count) * 100 if total_count else 0.0
        )
        print(f"Percentage of non-null values in 'value': {percentage_non_null:.2f}%")
        self.percentage_non_null = percentage_non_null
        return self.percentage_non_null