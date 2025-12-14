import streamlit as st
import pandas as pd
import altair as alt
import os

SERIES_META = {
    "CES0000000001": {
        "label": "Nonfarm Employment",
        "full": "Total Nonfarm Employment",
        "units": "THOUSANDS of Jobs",
        "color": "#1f77b4",  # blue
        "help": "All Employees on Nonfarm Payrolls (seasonally adjusted).",
        "unit_group": "Thousands",
    },
    "LNS14000000": {
        "label": "Unemployment Rate",
        "full": "Unemployment Rate",
        "units": "PERCENT",
        "color": "#d62728",  # red
        "help": "Percent of the Labor Force that is Unemployed.",
        "unit_group": "Percent",
    },
    "LNS11300000": {
        "label": "Participation Rate",
        "full": "Labor Force Participation Rate",
        "units": "PERCENT",
        "color": "#2ca02c",  # green
        "help": "Share of the Working-Age Population that is in the Labor Force.",
        "unit_group": "Percent",
    },
    "JTS000000000000000JOL": {
        "label": "Job Openings",
        "full": "Job Openings (JOLTS, Total Nonfarm)",
        "units": "THOUSANDS of Openings",
        "color": "#ff7f0e",  # orange
        "help": "Total Nonfarm Job Openings from the JOLTS Survey.",
        "unit_group": "Thousands",
    },
}


@st.cache_data
def load_data(_mtime: float):
    df = pd.read_csv("data/bls_labor_data.csv", parse_dates=["date"])
    return df


def render_color_key(selected_ids):
    """Small colored key so the user can map series -> color."""
    items = []
    for sid in selected_ids:
        meta = SERIES_META[sid]
        items.append(
            "<span style='display:inline-flex;align-items:center;margin-right:14px;'>"
            f"<span style='width:10px;height:10px;border-radius:50%;background:{meta['color']};"
            "display:inline-block;margin-right:6px;'></span>"
            f"{meta['label']}"
            "</span>"
        )
    st.markdown(" ".join(items), unsafe_allow_html=True)


def build_chart(df_plot, selected_ids, y_title):
    df_plot = df_plot.copy()
    df_plot["Series"] = df_plot["series_id"].map(lambda x: SERIES_META[x]["label"])

    domain = [SERIES_META[s]["label"] for s in selected_ids]
    rng = [SERIES_META[s]["color"] for s in selected_ids]
    color_scale = alt.Scale(domain=domain, range=rng)

    x_axis = alt.Axis(
        title="Date",
        format="%b %Y",
        labelAngle=0,
        tickCount=8,
    )

    chart = (
        alt.Chart(df_plot)
        .mark_line()
        .encode(
            x=alt.X("date:T", axis=x_axis),
            y=alt.Y("value:Q", title=y_title),
            color=alt.Color(
                "Series:N",
                scale=color_scale,
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("Series:N"),
                alt.Tooltip("date:T", title="Date", format="%B %Y"),
                alt.Tooltip("value:Q", title="Value", format=",.2f"),
            ],
        )
        .properties(height=360)
    )
    return chart


def main():
    st.title("U.S. Labor Market Dashboard")
    st.caption("Data source: U.S. Bureau of Labor Statistics (BLS)")

    mtime = os.path.getmtime("data/bls_labor_data.csv")
    df = load_data(mtime)

    latest_date = df["date"].max().date()
    st.write(f"Latest Data Month: **{latest_date}**")

    # ---- KPIs (2x2 so labels don't get squished) ----
    st.subheader("Latest Indicators")

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

    # Best-practice separation between KPI section and charts
    st.divider()

    # ---- Sidebar Controls ----
    st.sidebar.header("Chart Controls")

    selected_ids = st.sidebar.multiselect(
        "Choose Series To Plot:",
        options=list(SERIES_META.keys()),
        default=["CES0000000001", "LNS14000000"],
        format_func=lambda x: SERIES_META[x]["full"],
    )

    months_back = st.sidebar.slider(
        "Show Last N Months:",
        12,
        120,
        60,
    )

    # ---- Time Series ----
    st.subheader("Time Series")

    if selected_ids:
        render_color_key(selected_ids)

        df_plot = df[df["series_id"].isin(selected_ids)].copy()
        cutoff = df_plot["date"].max() - pd.DateOffset(months=months_back)
        df_plot = df_plot[df_plot["date"] >= cutoff]

        # Split selected series by unit group
        thousands_ids = [sid for sid in selected_ids if SERIES_META[sid]["unit_group"] == "Thousands"]
        percent_ids = [sid for sid in selected_ids if SERIES_META[sid]["unit_group"] == "Percent"]

        if thousands_ids:
            st.markdown("### Levels (Thousands)")
            df_thousands = df_plot[df_plot["series_id"].isin(thousands_ids)]
            chart_thousands = build_chart(df_thousands, thousands_ids, y_title="Thousands")
            st.altair_chart(chart_thousands, use_container_width=True)

        if percent_ids:
            st.markdown("### Rates (Percent)")
            df_percent = df_plot[df_plot["series_id"].isin(percent_ids)]
            chart_percent = build_chart(df_percent, percent_ids, y_title="Percent")
            st.altair_chart(chart_percent, use_container_width=True)

    else:
        st.info("Please Select At Least One Series In The Sidebar To Display The Charts.")


if __name__ == "__main__":
    main()