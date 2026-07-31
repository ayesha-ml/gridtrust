import logging
import os

import joblib
import numpy as np
import pandas as pd

from src.config import FEATURES, REGIONS

logger = logging.getLogger(__name__)


def load_objects(respondent):
    """
    Load trained models and evaluation datasets.
    """

    lower_model = joblib.load(
        f"models/{respondent.lower()}_lower.pkl"
    )

    upper_model = joblib.load(
        f"models/{respondent.lower()}_upper.pkl"
    )

    calibration = pd.read_csv(
        f"outputs/{respondent.lower()}_calibration.csv"
    )

    test = pd.read_csv(
        f"outputs/{respondent.lower()}_test.csv"
    )

    return (
        lower_model,
        upper_model,
        calibration,
        test,
    )


def calculate_nonconformity(
    lower_pred,
    upper_pred,
    actual,
):
    """
    Compute conformal nonconformity scores.
    """

    lower_error = lower_pred - actual
    upper_error = actual - upper_pred

    scores = np.maximum.reduce(
        [
            lower_error,
            upper_error,
            np.zeros(len(actual)),
        ]
    )

    return scores


def calculate_q_hat(scores, alpha=0.10):
    """
    Compute conformal calibration constant.
    """

    return np.quantile(
        scores,
        1 - alpha,
        method="higher",
    )


def apply_conformal(
    lower_pred,
    upper_pred,
    q_hat,
):
    """
    Expand prediction interval using conformal calibration.
    """

    lower = lower_pred - q_hat
    upper = upper_pred + q_hat

    return lower, upper


def evaluate_coverage(
    actual,
    lower,
    upper,
):
    """
    Evaluate empirical coverage and average interval width.
    """

    inside_interval = (
        (actual >= lower)
        & (actual <= upper)
    )

    coverage = inside_interval.mean()

    average_width = (
        upper - lower
    ).mean()

    return coverage, average_width


if __name__ == "__main__":

    TARGET_COVERAGE = 0.90

    results = []

    for region in REGIONS:

        logger.info("=" * 70)
        logger.info(
            "Running conformal prediction for %s",
            region,
        )
        logger.info("=" * 70)

        (
            lower_model,
            upper_model,
            calibration,
            test,
        ) = load_objects(region)

        X_calibration = calibration[FEATURES]
        y_calibration = calibration["demand"]

        lower_calibration = lower_model.predict(
            X_calibration
        )

        upper_calibration = upper_model.predict(
            X_calibration
        )

        scores = calculate_nonconformity(
            lower_calibration,
            upper_calibration,
            y_calibration,
        )

        q_hat = calculate_q_hat(scores)

        X_test = test[FEATURES]
        y_test = test["demand"]

        lower_test = lower_model.predict(
            X_test
        )

        upper_test = upper_model.predict(
            X_test
        )

        raw_inside = (
            (y_test >= lower_test)
            & (y_test <= upper_test)
        )

        raw_coverage = raw_inside.mean()

        raw_width = (
            upper_test - lower_test
        ).mean()

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

        coverage_gap = (
            TARGET_COVERAGE - coverage
        )

        logger.info(
            "Calibration rows : %d",
            len(calibration),
        )
        logger.info(
            "Test rows        : %d",
            len(test),
        )
        logger.info(
            "Raw coverage     : %.2f%%",
            raw_coverage * 100,
        )
        logger.info(
            "Raw width        : %.2f",
            raw_width,
        )
        logger.info(
            "q_hat            : %.2f",
            q_hat,
        )
        logger.info(
            "Coverage         : %.2f%%",
            coverage * 100,
        )
        logger.info(
            "Coverage gap     : %.2f%%",
            coverage_gap * 100,
        )
        logger.info(
            "Average width    : %.2f",
            average_width,
        )

        results.append(
            {
                "region": region,
                "q_hat": q_hat,
                "coverage": coverage,
                "coverage_gap": coverage_gap,
                "average_width": average_width,
            }
        )

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

        os.makedirs(
            "outputs",
            exist_ok=True,
        )

        output.to_csv(
            f"outputs/{region.lower()}_conformal_predictions.csv",
            index=False,
        )

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        "outputs/conformal_summary.csv",
        index=False,
    )

    logger.info("=" * 70)
    logger.info(
        "CONFORMAL PREDICTION SUMMARY"
    )
    logger.info("=" * 70)
    logger.info(
        "\n%s",
        results_df.to_string(
            index=False,
            formatters={
                "q_hat": "{:.2f}".format,
                "coverage": "{:.2%}".format,
                "coverage_gap": "{:.2%}".format,
                "average_width": "{:.2f}".format,
            },
        ),
    )