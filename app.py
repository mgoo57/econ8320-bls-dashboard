import streamlit as st
import pandas as pd
import altair as alt

# --- Series metadata ---
SERIES_META = {
    "CES0000000001": {
        "label": "Total nonfarm employment",
        "units": "Thousands of jobs",
        "color": "#1f77b4",  # blue
        "help": "All employees on nonfarm payrolls (seasonally adjusted)."
    },
    "LNS14000000": {
        "label": "Unemployment rate",
        "units": "Percent",
        "color": "#d62728",  # red
        "help": "Percent of the labor force that is unemployed."
    },
    "LNS11300000": {
        "label": "Labor force participation rate",
        "units": "Percent",
        "color": "#2ca02c",  # green
        "help": "Share of the working-age population that is in the labor force."
    },
    "JTS000000000000000JOL": {
        "label": "Job openings",
        "units": "Thousands of openings",
        "color": "#ff7f0e",  # orange
        "help": "Total nonfarm job openings from the JOLTS survey."
    },
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

    # ---- Latest indicators (KPIs) ----
    st.subheader("Latest indicators")

    latest = (
        df.sort_values("date")
        .groupby("series_id")
        .tail(1)
    )

    cols = st.columns(len(SERIES_META))
    for col, series_id in zip(cols, SERIES_META.keys()):
        row = latest[latest["series_id"] == series_id].iloc[0]
        meta = SERIES_META[series_id]

        with col:
            st.metric(
                label=meta["label"],
                value=f"{row['value']:.2f}",
                help=f"{meta['help']} Units: {meta['units']}"
            )

    # ---- Time series ----
    st.subheader("Time series")

    selected_series = st.multiselect(
        "Choose series to plot:",
        options=list(SERIES_META.keys()),
        default=["CES0000000001", "LNS14000000"],
        format_func=lambda x: SERIES_META[x]["label"],
    )

    months_back = st.slider("Show last N months:", 12, 120, 60)

    if selected_series:
        df_plot = df[df["series_id"].isin(selected_series)].copy()
        cutoff = df_plot["date"].max() - pd.DateOffset(months=months_back)
        df_plot = df_plot[df_plot["date"] >= cutoff]

        df_plot["Series"] = df_plot["series_id"].map(
            lambda x: SERIES_META[x]["label"]
        )

        color_scale = alt.Scale(
            domain=[SERIES_META[s]["label"] for s in selected_series],
            range=[SERIES_META[s]["color"] for s in selected_series],
        )

        chart = (
            alt.Chart(df_plot)
            .mark_line()
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("value:Q", title=""),
                color=alt.Color("Series:N", scale=color_scale),
                tooltip=[
                    alt.Tooltip("Series:N"),
                    alt.Tooltip("date:T", title="Date"),
                    alt.Tooltip("value:Q", title="Value", format=",.2f"),
                ],
            )
            .properties(height=400)
        )

        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()