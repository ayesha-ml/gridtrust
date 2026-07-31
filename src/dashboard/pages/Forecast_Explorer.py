import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Forecast Explorer",
    page_icon=None,
    layout="wide",
)

st.title("Forecast Explorer")
st.caption("Inspect probabilistic electricity demand forecasts by balancing authority.")

# ---------------------------------------------------
# load data
# ---------------------------------------------------

OUTPUT_DIR = Path("outputs")

regions = {
    "California ISO (CISO)": "ciso",
    "ERCOT (ERCO)": "erco",
    "PJM Interconnection": "pjm",
}

selected_region = st.sidebar.selectbox(
    "Balancing Authority",
    list(regions.keys()),
)

region = regions[selected_region]

df = pd.read_csv(
    OUTPUT_DIR / f"{region}_conformal_predictions.csv"
)

# ---------------------------------------------------
# date formatting
# ---------------------------------------------------

if "period" in df.columns:
    df["period"] = pd.to_datetime(df["period"])

# ---------------------------------------------------
# controls
# ---------------------------------------------------

window = st.sidebar.slider(
    "Number of observations",
    min_value=48,
    max_value=min(len(df), 500),
    value=min(len(df), 168),
    step=24,
)

plot_df = df.tail(window)

# ---------------------------------------------------
# metrics
# ---------------------------------------------------

left, middle, right = st.columns(3)

left.metric(
    "Observations",
    len(plot_df),
)

middle.metric(
    "Average Demand",
    f"{plot_df['actual'].mean():,.0f} MW",
)

right.metric(
    "Average Interval Width",
    f"{plot_df['interval_width'].mean():,.0f} MW",
)

st.divider()

# ---------------------------------------------------
# forecast chart
# ---------------------------------------------------

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=plot_df["period"],
        y=plot_df["actual"],
        mode="lines",
        name="Actual Demand",
        line=dict(width=2),
    )
)

fig.add_trace(
    go.Scatter(
        x=plot_df["period"],
        y=plot_df["lower_prediction"],
        mode="lines",
        name="Raw Lower",
        line=dict(dash="dot"),
        visible="legendonly",
    )
)

fig.add_trace(
    go.Scatter(
        x=plot_df["period"],
        y=plot_df["upper_prediction"],
        mode="lines",
        name="Raw Upper",
        line=dict(dash="dot"),
        visible="legendonly",
    )
)

fig.add_trace(
    go.Scatter(
        x=plot_df["period"],
        y=plot_df["conformal_upper"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
    )
)

fig.add_trace(
    go.Scatter(
        x=plot_df["period"],
        y=plot_df["conformal_lower"],
        mode="lines",
        fill="tonexty",
        name="90% Prediction Interval",
        line=dict(width=0),
    )
)

fig.update_layout(
    height=600,
    xaxis_title="Time",
    yaxis_title="Demand (MW)",
    legend_title=None,
    template="plotly_white",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

# ---------------------------------------------------
# interval diagnostics
# ---------------------------------------------------

st.subheader("Prediction Details")

display_columns = [
    "period",
    "actual",
    "conformal_lower",
    "conformal_upper",
    "interval_width",
    "inside_interval",
]

st.dataframe(
    plot_df[display_columns],
    use_container_width=True,
)

# ---------------------------------------------------
# download
# ---------------------------------------------------

st.download_button(
    "Download Forecast Results",
    plot_df.to_csv(index=False),
    file_name=f"{region}_forecast.csv",
    mime="text/csv",
)