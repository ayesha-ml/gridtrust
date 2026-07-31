import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Pipeline Monitoring",
    page_icon=None,
    layout="wide",
)

st.title("Pipeline Monitoring")
st.caption(
    "Operational status of the GRIDTRUST forecasting pipeline."
)

OUTPUT_DIR = Path("outputs")
MODEL_DIR = Path("models")

# ----------------------------------------------------------
# helper functions
# ----------------------------------------------------------

def file_modified(path):

    return datetime.fromtimestamp(
        path.stat().st_mtime
    )


regions = [
    "ciso",
    "erco",
    "pjm",
]

pipeline = []

for region in regions:

    prediction_file = (
        OUTPUT_DIR /
        f"{region}_conformal_predictions.csv"
    )

    lower_model = (
        MODEL_DIR /
        f"{region}_lower.pkl"
    )

    upper_model = (
        MODEL_DIR /
        f"{region}_upper.pkl"
    )

    pipeline.append(
        {
            "Region": region.upper(),
            "Predictions": prediction_file.exists(),
            "Lower Model": lower_model.exists(),
            "Upper Model": upper_model.exists(),
            "Last Updated":
                file_modified(prediction_file)
                if prediction_file.exists()
                else None,
        }
    )

pipeline = pd.DataFrame(pipeline)

# ----------------------------------------------------------
# overall metrics
# ----------------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Regions",
    len(pipeline),
)

col2.metric(
    "Models Available",
    int(
        pipeline["Lower Model"].sum()
    ),
)

col3.metric(
    "Prediction Files",
    int(
        pipeline["Predictions"].sum()
    ),
)

st.divider()

# ----------------------------------------------------------
# pipeline status
# ----------------------------------------------------------

st.subheader("Pipeline Status")

status = pipeline.copy()

status["Predictions"] = status["Predictions"].map(
    lambda x: "Available" if x else "Missing"
)

status["Lower Model"] = status["Lower Model"].map(
    lambda x: "Available" if x else "Missing"
)

status["Upper Model"] = status["Upper Model"].map(
    lambda x: "Available" if x else "Missing"
)

st.dataframe(
    status,
    hide_index=True,
    use_container_width=True,
)

# ----------------------------------------------------------
# output artifacts
# ----------------------------------------------------------

st.subheader("Generated Artifacts")

artifacts = []

for file in sorted(OUTPUT_DIR.glob("*")):

    artifacts.append(
        {
            "File": file.name,
            "Size (KB)": round(
                file.stat().st_size / 1024,
                2,
            ),
            "Modified":
                file_modified(file),
        }
    )

artifacts = pd.DataFrame(artifacts)

st.dataframe(
    artifacts,
    hide_index=True,
    use_container_width=True,
)

# ----------------------------------------------------------
# trained models
# ----------------------------------------------------------

st.subheader("Registered Models")

models = []

for file in sorted(MODEL_DIR.glob("*.pkl")):

    models.append(
        {
            "Model": file.name,
            "Size (KB)": round(
                file.stat().st_size / 1024,
                2,
            ),
            "Modified":
                file_modified(file),
        }
    )

models = pd.DataFrame(models)

st.dataframe(
    models,
    hide_index=True,
    use_container_width=True,
)

# ----------------------------------------------------------
# latest execution
# ----------------------------------------------------------

st.subheader("Latest Pipeline Execution")

latest = max(
    artifacts["Modified"]
)

st.success(
    f"Latest successful pipeline execution: {latest}"
)