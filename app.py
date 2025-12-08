import streamlit as st
import pandas as pd

SERIES_LABELS = {
    "CES0000000001": "Total nonfarm employment (thousands)",
    "LNS14000000": "Unemployment rate (%)",
    "LNS11300000": "Labor force participation rate (%)",
    "JTS000000000000000JOL": "Job openings, total nonfarm (thousands)",
}

@st.cache_data
def load_data():
    return pd.read_csv("data/bls_labor_data.csv", parse_dates=["date"])

def main():
    st.title("U.S. Labor Market Dashboard")
    st.caption("Data source: U.S. Bureau of Labor Statistics (BLS)")

    df = load_data()

    latest_date = df["date"].max().date()
    st.write(f"Latest data month: **{latest_date}**")

    # ---- Latest snapshot KPIs ----
    st.subheader("Latest indicators")
    latest = (
        df.sort_values("date")
        .groupby("series_id")
        .tail(1)
        .assign(label=lambda x: x["series_id"].map(SERIES_LABELS))
    )

    cols = st.columns(len(latest))
    for col, (_, row) in zip(cols, latest.iterrows()):
        with col:
            st.metric(row["label"], f"{row['value']:.2f}")

    # ---- Time series explorer ----
    st.subheader("Time series")

    series_choices = st.multiselect(
        "Choose series to plot:",
        options=list(SERIES_LABELS.keys()),
        default=["CES0000000001", "LNS14000000"],
        format_func=lambda x: SERIES_LABELS[x],
    )

    months_back = st.slider("Show last N months:", 12, 120, 60)

    if series_choices:
        df_plot = df[df["series_id"].isin(series_choices)].copy()
        cutoff = df_plot["date"].max() - pd.DateOffset(months=months_back)
        df_plot = df_plot[df_plot["date"] >= cutoff]

        df_plot["label"] = df_plot["series_id"].map(SERIES_LABELS)
        df_wide = df_plot.pivot(index="date", columns="label", values="value")

        st.line_chart(df_wide)

if __name__ == "__main__":
    main()