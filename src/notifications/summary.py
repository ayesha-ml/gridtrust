from google import genai
from dotenv import load_dotenv
import os


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing")


client = genai.Client(
    api_key=api_key
)

def generate_summary(report):

    summary = report["summary"]
    ingestion = report["ingestion"]
    coverage = report["coverage"]
    forecasts = report["forecasts"]

    prompt = f"""
You are an energy operations analyst.

Generate a concise executive summary for the GRIDTRUST electricity demand forecasting system.

Overall Pipeline Summary
------------------------
Total rows ingested: {summary["total_rows"]}
Regions monitored: {summary["regions"]}

Ingestion Status
----------------
{ingestion.to_markdown(index=False)}

Conformal Prediction Summary
----------------------------
{coverage.to_markdown(index=False)}

Latest Forecast Results
-----------------------
{forecasts.to_markdown(index=False)}

Write:

1. Overall pipeline health
2. Forecast reliability
3. Any observations supported by the data
4. Recommended monitoring action

Rules:
- Use ONLY the information provided.
- Never invent measurements, sensors, maintenance actions, or future events.
- If everything looks normal, clearly state that.
- Keep the response under 150 words.
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    return response.text


    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )


    return response.text