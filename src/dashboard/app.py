import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DATABASE_URL


st.set_page_config(
    page_title="GRIDTRUST",
    page_icon=None,
    layout="wide",
)

st.title("GRIDTRUST")
st.caption(
    "Electricity Demand Forecasting with Distribution-Free Prediction Intervals"
)


@st.cache_data(ttl=300)
def load_summary():

    conn = psycopg2.connect(DATABASE_URL)

    query = """
    SELECT
        respondent,
        COUNT(*) AS observations,
        MIN(period) AS start_date,
        MAX(period) AS end_date,
        AVG(value) AS average_demand
    FROM raw.electricity_demand
    GROUP BY respondent
    ORDER BY respondent;
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


summary = load_summary()


st.markdown("---")

st.subheader("System Overview")

left, middle, right = st.columns(3)

with left:

    st.metric(
        "Regions",
        len(summary),
    )

with middle:

    st.metric(
        "Total Observations",
        f"{summary['observations'].sum():,}",
    )

with right:

    st.metric(
        "Average Demand",
        f"{summary['average_demand'].mean():,.0f} MW",
    )


st.markdown("---")

st.subheader("Coverage Summary")

try:

    coverage = pd.read_csv(
        "outputs/conformal_summary.csv"
    )

    st.dataframe(
        coverage,
        use_container_width=True,
        hide_index=True,
    )

except FileNotFoundError:

    st.info(
        "Run the forecasting pipeline to generate conformal results."
    )


st.markdown("---")

st.subheader("Data Availability")

st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True,
)


st.markdown("---")

st.subheader("Pipeline")

pipeline = pd.DataFrame(
    {
        "Stage": [
            "Data Ingestion",
            "Feature Engineering",
            "Quantile Models",
            "Conformal Prediction",
        ],
        "Status": [
            "Completed",
            "Completed",
            "Completed",
            "Completed",
        ],
    }
)

st.dataframe(
    pipeline,
    use_container_width=True,
    hide_index=True,
)