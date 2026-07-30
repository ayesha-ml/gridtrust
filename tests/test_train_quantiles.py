import pandas as pd

from src.models.train_quantiles import time_series_split


def test_time_series_split_sizes():

    df = pd.DataFrame(
        {
            "value": range(100),
        }
    )

    train, calibration, test = time_series_split(df)

    assert len(train) == 70
    assert len(calibration) == 20
    assert len(test) == 10


def test_time_series_split_order():

    df = pd.DataFrame(
        {
            "value": range(100),
        }
    )

    train, calibration, test = time_series_split(df)

    assert train["value"].max() < calibration["value"].min()

    assert calibration["value"].max() < test["value"].min()