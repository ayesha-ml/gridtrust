from pathlib import Path

import pandas as pd
import psycopg2

from src.config import DATABASE_URL

OUTPUTS = Path("outputs")


def generate_report():

    conn = psycopg2.connect(DATABASE_URL)

    ingestion = pd.read_sql(
        """
        SELECT
            respondent,
            COUNT(*) AS rows_ingested,
            MAX(period) AS latest_timestamp
        FROM raw.electricity_demand
        GROUP BY respondent
        ORDER BY respondent;
        """,
        conn,
    )

    conn.close()

    coverage = pd.read_csv(
        OUTPUTS / "conformal_summary.csv"
    )

    forecasts = []

    for region in ["ciso", "erco", "pjm"]:

        df = pd.read_csv(
            OUTPUTS / f"{region}_conformal_predictions.csv"
        )

        latest = df.iloc[-1]

        forecasts.append(
            {
                "Region": region.upper(),
                "Actual": round(latest["actual"], 2),
                "Lower": round(latest["conformal_lower"], 2),
                "Upper": round(latest["conformal_upper"], 2),
                "Width": round(latest["interval_width"], 2),
                "Inside Interval": "Yes" if latest["inside_interval"] else "No",
            }
        )

    forecasts = pd.DataFrame(forecasts)

    report_summary = {
    "total_rows": int(ingestion["rows_ingested"].sum()),
    "regions": len(ingestion),
    }
    

    return {
    "summary": report_summary,
    "ingestion": ingestion,
    "coverage": coverage,
    "forecasts": forecasts,
    }