# scripts/fetch_bls_data.py
import os
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Keep series consistent with build_dataset.py
SERIES_IDS = [
    "CES0000000001",          # Total nonfarm employment
    "LNS14000000",            # Unemployment rate
    "LNS11300000",            # Labor force participation rate
    "JTS000000000000000JOL",  # Job openings: total nonfarm
]

DATA_PATH = Path("data/bls_labor_data.csv")


def fetch_latest(series_ids, start_year, end_year):
    """Fetch data for given series between start_year and end_year."""
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
    }

    api_key = os.getenv("BLS_API_KEY")
    if api_key:
        payload["registrationkey"] = api_key

    resp = requests.post(BLS_API_URL, json=payload)
    resp.raise_for_status()
    data = resp.json()

    # --- New defensive checks ---
    status = data.get("status")
    if status != "REQUEST_SUCCEEDED":
        print("BLS API request failed. Status:", status)
        print("Message:", data.get("message"))
        # Return empty DataFrame so caller can decide what to do
        return pd.DataFrame(columns=["series_id", "date", "value"])

    results = data.get("Results", {})
    series_list = results.get("series")
    if not series_list:
        print("BLS API returned no 'series' data. Full response:")
        print(data)
        return pd.DataFrame(columns=["series_id", "date", "value"])
    # --- end new checks ---

    rows = []
    for series in series_list:
        sid = series["seriesID"]
        for item in series["data"]:
            period = item["period"]  # 'M01'...'M12' or 'M13'
            if not period.startswith("M"):
                continue  # skip annual summary rows

            year = item["year"]
            month = period[1:]
            date_str = f"{year}-{month}-01"
            value = float(item["value"])
            rows.append(
                {
                    "series_id": sid,
                    "date": date_str,
                    "value": value,
                }
            )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Base dataset not found. Run scripts/build_dataset.py once before using fetch_bls_data.py."
        )

    # Load existing data
    df_existing = pd.read_csv(DATA_PATH, parse_dates=["date"])
    last_date = df_existing["date"].max()
    print(f"Last date in existing dataset: {last_date.date()}")

    # Fetch from the last year we have to current year
    start_year = last_date.year
    current_year = datetime.now().year

    print(f"Requesting BLS data from {start_year} to {current_year}...")
    df_new = fetch_latest(SERIES_IDS, start_year, current_year)

    # Filter to only dates AFTER the last existing date
    df_new = df_new[df_new["date"] > last_date]

    if df_new.empty:
        print("No new data available; dataset is already up to date.")
        return

    print(f"Fetched {len(df_new)} new rows.")

    # Combine and dedupe
    df_combined = (
        pd.concat([df_existing, df_new], ignore_index=True)
        .drop_duplicates(subset=["series_id", "date"])
        .sort_values(["series_id", "date"])
    )

    df_combined.to_csv(DATA_PATH, index=False)
    print(f"Updated dataset saved to {DATA_PATH} ({len(df_combined)} total rows).")


if __name__ == "__main__":
    main()