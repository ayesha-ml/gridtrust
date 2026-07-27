import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("EIA_API_KEY")
DB_URL = os.getenv("DATABASE_URL")
URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
REGIONS = ["CISO","ERCO","PJM"]

print("API KEY LOADED:", API_KEY is not None)
print("DATABASE URL LOADED:", DB_URL is not None)

def fetch_region(respondent, length=5000):
    params = {
        "api_key": API_KEY,
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": respondent,
        "facets[type][]": "D",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": length,
    }
    response = requests.get(URL, params=params)
    response.raise_for_status()
    return response.json()["response"]["data"]

def insert_rows(rows):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for row in rows:
        period = datetime.strptime(
            row["period"],
            "%Y-%m-%dT%H"
        )

        cur.execute("""
            INSERT INTO raw.electricity_demand
                (respondent, period, value)
            VALUES (%s, %s, %s)
            ON CONFLICT (respondent, period) DO NOTHING
        """,
        (
            row["respondent"],
            period,
            row["value"]
        ))

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    for region in REGIONS:
        print(f"Fetching {region}...")
        data = fetch_region(region)
        insert_rows(data)
        print(f"Inserted {len(data)} rows for {region}")