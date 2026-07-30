import os
import logging
import joblib
import pandas as pd
import psycopg2

from dotenv import load_dotenv
from lightgbm import LGBMRegressor

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

from src.config import (
    FEATURES,
    REGIONS,
    TRAIN_RATIO,
    CALIBRATION_RATIO,
    TEST_RATIO,
    LOWER_ALPHA,
    UPPER_ALPHA,
    N_ESTIMATORS,
    LEARNING_RATE,
    RANDOM_STATE,
    MODEL_DIR,
    OUTPUT_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def load_features(respondent):

    conn = psycopg2.connect(DB_URL)

    query = """
        SELECT *
        FROM features.demand_features
        WHERE respondent = %s
          AND lag_168h IS NOT NULL
        ORDER BY period
    """

    df = pd.read_sql(query, conn, params=(respondent,))

    conn.close()

    return df


def time_series_split(df):

    if abs(TRAIN_RATIO + CALIBRATION_RATIO + TEST_RATIO - 1.0) > 1e-9:
        raise ValueError("Split ratios must sum to 1.0")

    train_end = int(len(df) * TRAIN_RATIO)

    calibration_end = int(
        len(df) * (TRAIN_RATIO + CALIBRATION_RATIO)
    )

    train = df.iloc[:train_end]
    calibration = df.iloc[train_end:calibration_end]
    test = df.iloc[calibration_end:]

    return train, calibration, test


def train_quantile_models(respondent):

    logger.info("Training quantile models for %s...", respondent)

    df = load_features(respondent)

    train, calibration, test = time_series_split(df)

    logger.info("Demand Distribution")

    logger.info("\nTrain\n%s", train["demand"].describe())

    logger.info("\nCalibration\n%s", calibration["demand"].describe())

    logger.info("\nTest\n%s", test["demand"].describe())

    X_train = train[FEATURES]
    y_train = train["demand"]

    lower_model = LGBMRegressor(
        objective="quantile",
        alpha=LOWER_ALPHA,
        n_estimators=N_ESTIMATORS,
        learning_rate=LEARNING_RATE,
        random_state=RANDOM_STATE,
        verbosity=-1,
    )

    upper_model = LGBMRegressor(
        objective="quantile",
        alpha=UPPER_ALPHA,
        n_estimators=N_ESTIMATORS,
        learning_rate=LEARNING_RATE,
        random_state=RANDOM_STATE,
        verbosity=-1,
    )

    lower_model.fit(X_train, y_train)
    upper_model.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    joblib.dump(
        lower_model,
        os.path.join(
            MODEL_DIR,
            f"{respondent.lower()}_lower.pkl",
        ),
    )

    joblib.dump(
        upper_model,
        os.path.join(
            MODEL_DIR,
            f"{respondent.lower()}_upper.pkl",
        ),
    )

    calibration.to_csv(
        os.path.join(
            OUTPUT_DIR,
            f"{respondent.lower()}_calibration.csv",
        ),
        index=False,
    )

    test.to_csv(
        os.path.join(
            OUTPUT_DIR,
            f"{respondent.lower()}_test.csv",
        ),
        index=False,
    )

    logger.info("Saved lower model")
    logger.info("Saved upper model")
    logger.info("Saved calibration dataset")
    logger.info("Saved test dataset")
    logger.info("Train rows: %d", len(train))
    logger.info("Calibration rows: %d", len(calibration))
    logger.info("Test rows: %d", len(test))


if __name__ == "__main__":

    for region in REGIONS:
        train_quantile_models(region)