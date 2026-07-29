import os
import joblib
import pandas as pd
import psycopg2

from dotenv import load_dotenv
from lightgbm import LGBMRegressor

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

FEATURES = [
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
]

REGIONS = ["CISO", "ERCO", "PJM"]

TRAIN_RATIO = 0.70
CALIBRATION_RATIO = 0.20
TEST_RATIO = 0.10


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

    print(f"\nTraining quantile models for {respondent}...")

    df = load_features(respondent)

    train, calibration, test = time_series_split(df)

    print("\nDemand Distribution")

    print("\nTrain")
    print(train["demand"].describe())

    print("\nCalibration")
    print(calibration["demand"].describe())

    print("\nTest")
    print(test["demand"].describe())

    X_train = train[FEATURES]
    y_train = train["demand"]

    lower_model = LGBMRegressor(
        objective="quantile",
        alpha=0.05,
        n_estimators=500,
        learning_rate=0.05,
        random_state=42,
        verbosity=-1,
    )

    upper_model = LGBMRegressor(
        objective="quantile",
        alpha=0.95,
        n_estimators=500,
        learning_rate=0.05,
        random_state=42,
        verbosity=-1,
    )

    lower_model.fit(X_train, y_train)
    upper_model.fit(X_train, y_train)

    os.makedirs("models", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    joblib.dump(lower_model,f"models/{respondent.lower()}_lower.pkl")

    joblib.dump(upper_model,f"models/{respondent.lower()}_upper.pkl")

    calibration.to_csv(f"outputs/{respondent.lower()}_calibration.csv",index=False,)

    test.to_csv(f"outputs/{respondent.lower()}_test.csv",index=False,)

    print("Saved lower model")
    print("Saved upper model")
    print("Saved calibration dataset")
    print("Saved test dataset")
    print(f"Train rows: {len(train)}")
    print(f"Calibration rows: {len(calibration)}")
    print(f"Test rows: {len(test)}")


if __name__ == "__main__":

    for region in REGIONS:
        train_quantile_models(region)