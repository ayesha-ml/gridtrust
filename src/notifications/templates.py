from datetime import datetime
from markdown import markdown


def build_email(report, ai_summary):

    ingestion = report["ingestion"]
    forecasts = report["forecasts"]
    coverage = report["coverage"]

    total_rows = report["summary"]["total_rows"]

    run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ingestion_rows = ""

    for _, row in ingestion.iterrows():

        ingestion_rows += f"""
        <tr>
            <td>{row["respondent"]}</td>
            <td>{row["rows_ingested"]:,}</td>
            <td>{row["latest_timestamp"]}</td>
        </tr>
        """

    forecast_rows = ""

    for _, row in forecasts.iterrows():

        forecast_rows += f"""
        <tr>
            <td>{row["Region"]}</td>
            <td>{row["Actual"]:,.0f}</td>
            <td>{row["Lower"]:,.0f}</td>
            <td>{row["Upper"]:,.0f}</td>
            <td>{row["Width"]:,.0f}</td>
            <td>{row["Inside Interval"]}</td>
        </tr>
        """

    coverage_table = coverage.to_html(
        index=False,
        border=0,
        classes="coverage-table",
    )

    html_summary = markdown(ai_summary)

    return f"""
<!DOCTYPE html>

<html>

<head>

<style>

body {{
    font-family: Arial, Helvetica, sans-serif;
    background: #f5f7fa;
    color: #333333;
    margin: 0;
    padding: 30px;
}}

.container {{
    max-width: 900px;
    margin: auto;
    background: white;
    padding: 35px;
    border: 1px solid #dddddd;
}}

h1 {{
    margin-bottom: 5px;
    color: #0B5394;
}}

h2 {{
    margin-top: 35px;
    color: #0B5394;
    border-bottom: 2px solid #0B5394;
    padding-bottom: 6px;
}}

.info {{
    margin-top: 20px;
    line-height: 1.8;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}}

th {{
    background: #0B5394;
    color: white;
    padding: 10px;
    text-align: left;
}}

td {{
    padding: 10px;
    border: 1px solid #dddddd;
}}

.summary {{
    background: #f2f6fb;
    border-left: 4px solid #0B5394;
    padding: 18px;
    margin-top: 15px;
    line-height: 1.6;
}}

.summary h3 {{
    margin-top: 0;
    color: #0B5394;
}}

.summary ul {{
    margin-top: 10px;
    padding-left: 20px;
}}

.summary p {{
    margin: 10px 0;
}}

.footer {{
    margin-top: 40px;
    font-size: 12px;
    color: gray;
    border-top: 1px solid #dddddd;
    padding-top: 15px;
}}

</style>

</head>

<body>

<div class="container">

<h1>GRIDTRUST</h1>

<p>Electricity Demand Forecast Report</p>

<div class="info">

<b>Run Time:</b> {run_time}<br>

<b>Pipeline Status:</b> Completed Successfully<br>

<b>Total Rows Processed:</b> {total_rows:,}

</div>

<h2>Data Ingestion</h2>

<table>

<tr>
<th>Region</th>
<th>Rows Ingested</th>
<th>Latest Timestamp</th>
</tr>

{ingestion_rows}

</table>

<h2>Prediction Results</h2>

<table>

<tr>
<th>Region</th>
<th>Actual</th>
<th>Lower Bound</th>
<th>Upper Bound</th>
<th>Interval Width</th>
<th>Inside Interval</th>
</tr>

{forecast_rows}

</table>

<h2>Model Performance</h2>

{coverage_table}

<h2>Executive Summary</h2>

<div class="summary">

{html_summary}

</div>

<div class="footer">

This report was generated automatically by the GRIDTRUST forecasting pipeline.

</div>

</div>

</body>

</html>
"""