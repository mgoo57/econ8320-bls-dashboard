import streamlit as st
import pandas as pd
import altair as alt

SERIES_META = {
    "CES0000000001": {
        "label": "Nonfarm Employment",
        "full": "Total Nonfarm Employment",
        "units": "Thousands of Jobs",
        "color": "#1f77b4",  # blue
        "help": "All Employees on Nonfarm Payrolls (seasonally adjusted).",
    },
    "LNS14000000": {
        "label": "Unemployment Rate",
        "full": "Unemployment Rate",
        "units": "Percent",
        "color": "#d62728",  # red
        "help": "Percent of the Labor Force that is Unemployed.",
    },
    "LNS11300000": {
        "label": "Participation Rate",
        "full": "Labor Force Participation Rate",
        "units": "Percent",
        "color": "#2ca02c",  # green
        "help": "Share of the Working-Age Population that is in the Labor Force.",
    },
    "JTS000000000000000JOL": {
        "label": "Job Openings",
        "full": "Job Openings (JOLTS, Total Nonfarm)",
        "units": "Thousands of Openings",
        "color": "#ff7f0e",  # orange
        "help": "Total Nonfarm Job Openings from the JOLTS Survey.",
    },
}

@st.cache_data
def load_data():
    df = pd.read_csv("data/bls_labor_data.csv", parse_dates=["date"])
    return df

def render_color_key(selected_ids):
    """Small colored key so the user can map series -> color."""
    items = []
    for sid in selected_ids:
        meta = SERIES_META[sid]
        items.append(
            f"<span style='display:inline-flex;align-items:center;margin-right:14px;'>"
            f"<span style='width:10px;height:10px;border-radius:50%;background:{meta['color']};display:inline-block;margin-right:6px;'></span>"
            f"{meta['label']}"
            f"</span>"
        )
    st.markdown(" ".join(items), unsafe_allow_html=True)

def build_chart(df_plot, selected_ids):
    df_plot = df_plot.copy()
    df_plot["Series"] = df_plot["series_id"].map(lambda x: SERIES_META[x]["label"])

    # Force consistent colors for selected series
    domain = [SERIES_META[s]["label"] for s in selected_ids]
    rng = [SERIES_META[s]["color"] for s in selected_ids]
    color_scale = alt.Scale(domain=domain, range=rng)

    # X-axis formatting: show year-month and tick about every 6 months
    x_axis = alt.Axis(
        title="Date",
        format="%b %Y",      # e.g., Oct 2025
        labelAngle=0,
        tickCount=8
    )

    chart = (
        alt.Chart(df_plot)
        .mark_line()
        .encode(
            x=alt.X("date:T", axis=x_axis),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color("Series:N", scale=color_scale, legend=alt.Legend(orient="top")),
            tooltip=[
                alt.Tooltip("Series:N"),
                alt.Tooltip("date:T", title="Date", format="%B %Y"),
                alt.Tooltip("value:Q", title="Value", format=",.2f"),
            ],
        )
        .properties(height=420)
    )
    return chart

def main():
    st.title("U.S. Labor Market Dashboard")
    st.caption("Data source: U.S. Bureau of Labor Statistics (BLS)")

    df = load_data()
    latest_date = df["date"].max().date()
    st.write(f"Latest data month: **{latest_date}**")

    # ---- KPIs (2x2 so labels don't get squished) ----
    st.subheader("Latest indicators")

    latest = df.sort_values("date").groupby("series_id").tail(1).set_index("series_id")

    kpi_order = list(SERIES_META.keys())
    row1 = kpi_order[:2]
    row2 = kpi_order[2:]

    c1, c2 = st.columns(2)
    for col, sid in zip([c1, c2], row1):
        meta = SERIES_META[sid]
        value = latest.loc[sid, "value"]
        col.metric(
            label=meta["full"],
            value=f"{value:.2f}",
            help=f"{meta['help']} Units: {meta['units']}",
        )

    c3, c4 = st.columns(2)
    for col, sid in zip([c3, c4], row2):
        meta = SERIES_META[sid]
        value = latest.loc[sid, "value"]
        col.metric(
            label=meta["full"],
            value=f"{value:.2f}",
            help=f"{meta['help']} Units: {meta['units']}",
        )

    # ---- Time series ----
    st.subheader("Time series")

    selected_ids = st.multiselect(
        "Choose series to plot:",
        options=list(SERIES_META.keys()),
        default=["CES0000000001", "LNS14000000"],
        format_func=lambda x: SERIES_META[x]["full"],  # shows full name in dropdown
    )

    months_back = st.slider("Show last N months:", 12, 120, 60)

    if selected_ids:
        # Color key (since Streamlit chips won't be multi-colored)
        render_color_key(selected_ids)

        df_plot = df[df["series_id"].isin(selected_ids)].copy()
        cutoff = df_plot["date"].max() - pd.DateOffset(months=months_back)
        df_plot = df_plot[df_plot["date"] >= cutoff]

        chart = build_chart(df_plot, selected_ids)
        st.altair_chart(chart, use_container_width=True)

        st.caption(
            "Note: different series use different units (%, thousands). "
            "For direct comparisons, select series with matching units."
        )

if __name__ == "__main__":
    main()