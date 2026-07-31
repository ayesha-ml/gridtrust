import logging
import subprocess
import time
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

def run_step(name, command):
    """
    Execute one pipeline stage.
    """

    logger.info("=" * 70)
    logger.info("Starting: %s", name)

    start_time = time.perf_counter()

    result = subprocess.run(command,capture_output=True,text=True,)

    elapsed = time.perf_counter() - start_time

    if result.returncode != 0:

        logger.error("%s failed.", name)

        if result.stderr:
            logger.error(result.stderr)

        raise RuntimeError(f"{name} failed.")

    if result.stdout.strip():
        logger.info("\n%s", result.stdout)

    logger.info(
        "%s completed successfully in %.2f seconds.",
        name,
        elapsed,
    )


if __name__ == "__main__":

    logger.info("=" * 70)
    logger.info("GRIDTRUST PIPELINE STARTED")
    logger.info("=" * 70)

    run_step(
    "Data Ingestion",
    [
        sys.executable,
        "-m",
        "src.data.ingest_EIA",
    ],
    )

    run_step(
        "Feature Engineering",
        [
            sys.executable,
            "-m",
            "src.features.build_features",
        ],
    )

    run_step(
        "Quantile Model Training",
        [
            sys.executable,
            "-m",
            "src.models.train_quantiles",
        ],
    )

    run_step(
        "Conformal Prediction",
        [
            sys.executable,
            "-m",
            "src.models.conformal_predict",
        ],
    )

    logger.info("=" * 70)
    logger.info("GRIDTRUST PIPELINE FINISHED SUCCESSFULLY")
    logger.info("=" * 70)


    