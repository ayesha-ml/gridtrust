import os
import joblib
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
REGIONS = ["CISO", "ERCO", "PJM"]

os.makedirs("models", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


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


def walk_forward_split(df, test_hours=168):
    """
    Most recent week is hold out for testing purpose.
    The model is trained on past data and is then evaluated on this.
    """

    split_point = len(df) - test_hours

    train = df.iloc[:split_point]
    test = df.iloc[split_point:]

    return train, test


def train_and_evaluate(respondent):

    print(f"\nTraining model for {respondent}...")

    df = load_features(respondent)

    # train/test split
    train, test = walk_forward_split(df)

    features = [
        "lag_1h",
        "lag_24h",
        "lag_168h",
        "hour_of_day",
        "day_of_week",
        "is_weekend",
    ]

    # separate inputs and target
    X_train = train[features]
    y_train = train["demand"]

    X_test = test[features]
    y_test = test["demand"]

    # training model
    model = LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=7,
        random_state=42,
        verbosity=-1,
    )

    model.fit(X_train, y_train)

    joblib.dump(
        model,
        f"models/{respondent.lower()}_baseline.pkl"
    )

    #predictions
    predictions = model.predict(X_test)

    prediction_df = pd.DataFrame({
        "period": test["period"],
        "actual": y_test,
        "prediction": predictions,
    })

    prediction_df["error"] = (
        prediction_df["actual"] - prediction_df["prediction"]
    )

    prediction_df.to_csv(
        f"outputs/{respondent.lower()}_predictions.csv",
        index=False,
    )

    importance = pd.DataFrame({
        "feature": features,
        "importance": model.feature_importances_
    })

    importance = importance.sort_values(
        by="importance",
        ascending=False
    )

    importance.to_csv(
        f"outputs/{respondent.lower()}_feature_importance.csv",
        index=False,
    )

    print(f"\nFeature Importance ({respondent})")
    print(importance)

    #evaluation
    mae = mean_absolute_error(y_test, predictions)
    rmse = root_mean_squared_error(y_test, predictions)

    return {
        "region": respondent,
        "total_rows": len(df),
        "train_rows": len(train),
        "test_rows": len(test),
        "mae": mae,
        "rmse": rmse,
    }


if __name__ == "__main__":

    results = []

    for region in REGIONS:
        result = train_and_evaluate(region)
        results.append(result)

    results_df = pd.DataFrame(results)

    print("\n")
    print("=" * 60)
    print("BASELINE MODEL RESULTS")
    print("=" * 60)

    print(
        results_df.to_string(
            index=False,
            formatters={
                "mae": "{:.2f}".format,
                "rmse": "{:.2f}".format,
            }
        )
    )