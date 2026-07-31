import logging
import psycopg2

from dotenv import load_dotenv

from src.config import DATABASE_URL

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def build_features():

    logger.info("=" * 60)
    logger.info("Building Feature Table")
    logger.info("=" * 60)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    with open(
        "src/features/build_features.sql",
        "r",
        encoding="utf-8",
    ) as file:

        sql = file.read()

    cur.execute(sql)

    conn.commit()

    cur.close()
    conn.close()

    logger.info("Feature table built successfully.")


if __name__ == "__main__":

    build_features()