from src.config import (
    REGIONS,
    FEATURES,
    TRAIN_RATIO,
    CALIBRATION_RATIO,
    TEST_RATIO,
    TARGET_COVERAGE,
)


def test_regions_not_empty():
    assert len(REGIONS) > 0


def test_feature_list_not_empty():
    assert len(FEATURES) > 0


def test_split_ratios_sum_to_one():
    total = TRAIN_RATIO + CALIBRATION_RATIO + TEST_RATIO
    assert total == 1.0


def test_target_coverage_valid():
    assert 0 < TARGET_COVERAGE < 1