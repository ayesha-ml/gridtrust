import logging
from datetime import datetime

import psycopg2
import requests

from src.config import (
    DATABASE_URL,
    EIA_API_KEY,
    EIA_BASE_URL,
    REGIONS,
    FETCH_LENGTH,
)

logger = logging.getLogger(__name__)


logger.info("API KEY LOADED: %s", EIA_API_KEY is not None)
logger.info("DATABASE URL LOADED: %s", DATABASE_URL is not None)

def fetch_region(respondent, length=FETCH_LENGTH):

    params = {
        "api_key": EIA_API_KEY,
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": respondent,
        "facets[type][]": "D",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": length,
    }

    response = requests.get(EIA_BASE_URL, params=params)

    response.raise_for_status()

    return response.json()["response"]["data"]


def insert_rows(rows):

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    for row in rows:

        period = datetime.strptime(
            row["period"],
            "%Y-%m-%dT%H",
        )

        cur.execute(
            """
            INSERT INTO raw.electricity_demand
                (respondent, period, value)
            VALUES (%s, %s, %s)
            ON CONFLICT (respondent, period) DO NOTHING
            """,
            (
                row["respondent"],
                period,
                row["value"],
            ),
        )

    conn.commit()

    cur.close()
    conn.close()


if __name__ == "__main__":

    for region in REGIONS:

        logger.info("Fetching %s...", region)

        data = fetch_region(region)

        insert_rows(data)

        logger.info("Inserted %d rows for %s", len(data), region)