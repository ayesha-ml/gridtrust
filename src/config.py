"""
config.py

central configuration for the GRIDTRUST project.

all project-wide constants and environment variables
are defined here so every module shares the same
configuration.
"""

import os

from dotenv import load_dotenv

# ----------------------------------------------------------
# load environment variables
# ----------------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
EIA_API_KEY = os.getenv("EIA_API_KEY")

# ----------------------------------------------------------
# eia configuration
# ----------------------------------------------------------

EIA_BASE_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"


REGIONS = [
    "CISO",
    "ERCO",
    "PJM",
]

FETCH_LENGTH = 50

# ----------------------------------------------------------
# feature engineering
# ----------------------------------------------------------

FEATURES = [
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
]

# ----------------------------------------------------------
# train / calibration / test split
# ----------------------------------------------------------

TRAIN_RATIO = 0.70
CALIBRATION_RATIO = 0.20
TEST_RATIO = 0.10

# ----------------------------------------------------------
# quantile regression
# ----------------------------------------------------------

LOWER_ALPHA = 0.05
UPPER_ALPHA = 0.95

N_ESTIMATORS = 300
LEARNING_RATE = 0.05
RANDOM_STATE = 42

# ----------------------------------------------------------
# conformal prediction
# ----------------------------------------------------------

TARGET_COVERAGE = 0.90
CONFORMAL_ALPHA = 0.10

# ----------------------------------------------------------
# output directories
# ----------------------------------------------------------

MODEL_DIR = "models"
OUTPUT_DIR = "outputs"
LOG_DIR = "logs"