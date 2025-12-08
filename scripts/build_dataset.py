# scripts/build_dataset.py
import os
import requests
import pandas as pd
from pathlib import Path

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Core series for the dashboard
SERIES_IDS = [
    "CES0000000001",          # Total nonfarm employment
    "LNS14000000",            # Unemployment rate
    "LNS11300000",            # Labor force participation rate
    "JTS000000000000000JOL",  # Job openings: total nonfarm
]

START_YEAR = "2015"
END_YEAR = "2025"  # adjust later if you want

def fetch_series(series_ids, start_year, end_year):
    payload = {
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year,
    }

    api_key = os.getenv("BLS_API_KEY")
    if api_key:
        payload["registrationkey"] = api_key

    resp = requests.post(BLS_API_URL, json=payload)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for series in data["Results"]["series"]:
        sid = series["seriesID"]
        for item in series["data"]:
            period = item["period"]
            if not period.startswith("M"):
                continue  # skip annual summaries

            year = item["year"]
            month = period[1:]
            date = f"{year}-{month}-01"
            value = float(item["value"])
            rows.append({"series_id": sid, "date": date, "value": value})

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df

def main():
    df = fetch_series(SERIES_IDS, START_YEAR, END_YEAR)
    df = df.sort_values(["series_id", "date"])

    Path("data").mkdir(exist_ok=True)
    df.to_csv("data/bls_labor_data.csv", index=False)
    print("Data saved to data/bls_labor_data.csv")

if __name__ == "__main__":
    main()