import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Model Performance",
    page_icon=None,
    layout="wide",
)

st.title("Model Performance")
st.caption(
    "Evaluate empirical coverage and uncertainty calibration."
)

OUTPUT_DIR = Path("outputs")

summary = pd.read_csv(
    OUTPUT_DIR / "conformal_summary.csv"
)

# --------------------------------------------------------
# metrics
# --------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Target Coverage",
    "90%",
)

col2.metric(
    "Average Coverage",
    f"{summary['coverage'].mean()*100:.2f}%"
)

col3.metric(
    "Average Width",
    f"{summary['average_width'].mean():,.0f} MW"
)

col4.metric(
    "Average q̂",
    f"{summary['q_hat'].mean():.2f}"
)

st.divider()

# --------------------------------------------------------
# coverage by region
# --------------------------------------------------------

st.subheader("Coverage by Region")

fig = px.bar(
    summary,
    x="region",
    y="coverage",
    text=summary["coverage"].map(lambda x: f"{x:.1%}"),
)

fig.add_hline(
    y=0.90,
    line_dash="dash",
    annotation_text="Target Coverage",
)

fig.update_layout(
    template="plotly_white",
    height=450,
    yaxis_title="Coverage",
    xaxis_title=None,
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

# --------------------------------------------------------
# interval width
# --------------------------------------------------------

st.subheader("Prediction Interval Width")

fig = px.bar(
    summary,
    x="region",
    y="average_width",
    text="average_width",
)

fig.update_layout(
    template="plotly_white",
    height=450,
    xaxis_title=None,
    yaxis_title="Average Width (MW)",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

# --------------------------------------------------------
# coverage gap
# --------------------------------------------------------

st.subheader("Coverage Gap")

fig = px.bar(
    summary,
    x="region",
    y="coverage_gap",
    text=summary["coverage_gap"].map(lambda x: f"{x:.1%}")
)

fig.update_layout(
    template="plotly_white",
    height=450,
    xaxis_title=None,
    yaxis_title="Gap",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

# --------------------------------------------------------
# summary table
# --------------------------------------------------------

st.subheader("Performance Summary")

display = summary.copy()

display["coverage"] = (
    display["coverage"] * 100
).round(2)

display["coverage_gap"] = (
    display["coverage_gap"] * 100
).round(2)

display["average_width"] = (
    display["average_width"]
).round(2)

display["q_hat"] = (
    display["q_hat"]
).round(2)

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
)