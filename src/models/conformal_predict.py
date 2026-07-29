import os
import joblib
import numpy as np
import pandas as pd

FEATURES = [
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
]

REGIONS = ["CISO", "ERCO", "PJM"]

def load_objects(respondent):
    """
    Load the saved models and datasets.
    """

    lower_model = joblib.load(f"models/{respondent.lower()}_lower.pkl")

    upper_model = joblib.load(f"models/{respondent.lower()}_upper.pkl")

    calibration = pd.read_csv(f"outputs/{respondent.lower()}_calibration.csv")

    test = pd.read_csv(f"outputs/{respondent.lower()}_test.csv")

    return lower_model, upper_model, calibration, test


def calculate_nonconformity(lower_pred, upper_pred, actual):

    lower_error = lower_pred - actual
    upper_error = actual - upper_pred

    scores = np.maximum.reduce([lower_error,upper_error,np.zeros(len(actual))])

    return scores


def calculate_q_hat(scores, alpha=0.10):
    """
    Compute the conformal calibration value.
    """
    q_hat = np.quantile(scores,1 - alpha,method="higher")

    return q_hat

def apply_conformal(lower_pred, upper_pred, q_hat):
    """
    Expand the prediction interval using the conformal calibration value.
    """

    lower = lower_pred - q_hat
    upper = upper_pred + q_hat

    return lower, upper

def evaluate_coverage(actual, lower, upper):
    """
    measures how often the true demand falls inside the conformal prediction interval.
    """

    inside_interval = ((actual >= lower) &(actual <= upper) )

    coverage = inside_interval.mean()

    average_width = (upper - lower).mean()

    return coverage, average_width
if __name__ == "__main__":

    TARGET_COVERAGE = 0.90

    results = []

    for region in REGIONS:

        print(f"\n{'=' * 60}")
        print(f"Running conformal prediction for {region}")
        print(f"{'=' * 60}")

        lower_model, upper_model, calibration, test = load_objects(region)

        X_calibration = calibration[FEATURES]
        y_calibration = calibration["demand"]

        lower_calibration = lower_model.predict(X_calibration)
        upper_calibration = upper_model.predict(X_calibration)

        scores = calculate_nonconformity(
            lower_calibration,
            upper_calibration,
            y_calibration,
        )

        q_hat = calculate_q_hat(scores)

        X_test = test[FEATURES]
        y_test = test["demand"]

        lower_test = lower_model.predict(X_test)
        upper_test = upper_model.predict(X_test)

        raw_inside = ((y_test >= lower_test) &(y_test <= upper_test))

        raw_coverage = raw_inside.mean()

        raw_width = (upper_test - lower_test).mean()

        print(f"Raw Coverage      : {raw_coverage:.2%}")
        print(f"Raw Interval Width: {raw_width:.2f}")

        lower_conformal, upper_conformal = apply_conformal(
            lower_test,
            upper_test,
            q_hat,
        )

        coverage, average_width = evaluate_coverage(
            y_test,
            lower_conformal,
            upper_conformal,
        )

        coverage_gap = TARGET_COVERAGE - coverage

        print(f"Calibration rows : {len(calibration)}")
        print(f"Test rows        : {len(test)}")
        print(f"q̂               : {q_hat:.2f}")
        print(f"Coverage         : {coverage:.2%}")
        print(f"Coverage Gap     : {coverage_gap:.2%}")
        print(f"Average Width    : {average_width:.2f}")

        results.append({
            "region": region,
            "q_hat": q_hat,
            "coverage": coverage,
            "coverage_gap": coverage_gap,
            "average_width": average_width,
        })

        output = test.copy()

        output["actual"] = y_test
        output["lower_prediction"] = lower_test
        output["upper_prediction"] = upper_test
        output["conformal_lower"] = lower_conformal
        output["conformal_upper"] = upper_conformal
        output["interval_width"] = (
            upper_conformal - lower_conformal
        )
        output["inside_interval"] = (
            (y_test >= lower_conformal)
            & (y_test <= upper_conformal)
        )

        os.makedirs("outputs", exist_ok=True)

        output.to_csv(
            f"outputs/{region.lower()}_conformal_predictions.csv",
            index=False,
        )

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        "outputs/conformal_summary.csv",
        index=False,
    )

    print("\n")
    print("=" * 70)
    print("CONFORMAL PREDICTION SUMMARY")
    print("=" * 70)

    print(
        results_df.to_string(
            index=False,
            formatters={
                "q_hat": "{:.2f}".format,
                "coverage": "{:.2%}".format,
                "coverage_gap": "{:.2%}".format,
                "average_width": "{:.2f}".format,
            },
        )
    )

    