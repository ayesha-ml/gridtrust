# GRIDTRUST System Design

## Overview

GRIDTRUST is an uncertainty-aware electricity demand forecasting system that combines quantile regression with conformal prediction to generate statistically valid prediction intervals for hourly electricity demand.

Unlike traditional forecasting systems that predict a single value, GRIDTRUST predicts a lower bound and an upper bound for future electricity demand. These prediction intervals provide operators with a measure of uncertainty, allowing better operational planning and risk management.

The system is fully automated through a reproducible machine learning pipeline that performs data ingestion, feature engineering, model training, conformal calibration, and artifact generation from a single command.

---

# 1. Project Goal

The primary objective of GRIDTRUST is to answer two questions:

> **What will electricity demand be?**

and

> **How confident are we in that prediction?**

Most forecasting systems provide only a point estimate.

Example:

| Forecast  | Actual    |
| --------- | --------- |
| 32,500 MW | 36,100 MW |

While useful, this prediction gives no indication of uncertainty.

GRIDTRUST instead predicts an interval.

Example:

| Lower     | Upper     | Actual    |
| --------- | --------- | --------- |
| 30,900 MW | 36,700 MW | 36,100 MW |

This interval communicates not only the prediction, but also the confidence surrounding it.

To accomplish this, the project combines:

- PostgreSQL for data storage
- SQL feature engineering
- LightGBM Quantile Regression
- Conformal Prediction
- Python automation
- Centralized configuration
- End-to-end reproducible pipelines

---

# 2. High-Level Architecture

The overall system architecture is shown below.

```text
                    ┌────────────────────┐
                    │     EIA API        │
                    │ Hourly Demand Data │
                    └─────────┬──────────┘
                              │
                              ▼
                   Data Ingestion (Python)
                              │
                              ▼
                PostgreSQL : raw.electricity_demand
                              │
                              ▼
                SQL Feature Engineering Pipeline
                              │
                              ▼
              features.demand_features Table
                              │
                              ▼
                LightGBM Quantile Regression
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
        Lower Quantile Model        Upper Quantile Model
                │                           │
                └─────────────┬─────────────┘
                              ▼
                  Conformal Calibration
                              │
                              ▼
                 Prediction Intervals
                              │
                              ▼
          CSV Outputs + Serialized Models (.pkl)
```

The architecture is intentionally modular.

Each stage has a single responsibility and can be executed independently or orchestrated through the master pipeline.

---

# 3. Repository Structure

The project follows a production-style directory layout where each component has a dedicated responsibility.

```text
gridtrust/

│
├── docs/
│       system_design.md
│
├── models/
│
├── outputs/
│
├── src/
│
│   ├── automation/
│   │       pipeline.py
│   │
│   ├── data/
│   │       ingest_EIA.py
│   │
│   ├── features/
│   │       build_features.py
│   │       build_features.sql
│   │
│   ├── models/
│   │       train_quantiles.py
│   │       conformal_predict.py
│   │
│   └── config.py
│
├── tests/
│
├── Dockerfile
│
├── requirements.txt
│
└── README.md
```

### docs/

Contains technical documentation describing the system architecture, engineering decisions, and implementation details.

---

### src/

Contains the entire application source code.

The project separates responsibilities into independent modules rather than placing all code into a single script.

---

### automation/

Responsible for orchestration.

The master pipeline executes every stage in the correct order while measuring runtime, handling failures, and providing centralized logging.

Current execution flow:

```text
pipeline.py

↓

Data Ingestion

↓

Feature Engineering

↓

Model Training

↓

Conformal Prediction
```

---

### data/

Responsible for collecting raw electricity demand data from the U.S. Energy Information Administration (EIA) API.

Responsibilities include:

- API communication
- Database insertion
- Duplicate prevention
- Raw data loading

---

### features/

Responsible for transforming raw hourly observations into machine learning features.

Feature engineering is intentionally performed inside PostgreSQL using SQL window functions rather than Python.

This keeps transformations reproducible and database-native.

---

### models/

Contains all machine learning logic.

Current modules include:

- Quantile model training
- Conformal prediction
- Interval evaluation

Separating training from calibration keeps each stage independent and easier to maintain.

---

### outputs/

Stores generated artifacts including:

- Prediction CSV files
- Calibration datasets
- Test datasets
- Feature importance reports
- Conformal prediction summaries

Outputs are regenerated every pipeline execution.

---

### models/

Stores serialized LightGBM models using Joblib.

Each region has independently trained lower and upper quantile models.

---

### config.py

Acts as the central configuration file for the project.

Instead of hardcoding constants throughout multiple files, every configurable value is defined once.

Examples include:

- API credentials
- Database connection
- Feature list
- Train/Calibration/Test split ratios
- Hyperparameters
- Forecast regions

Centralizing configuration improves maintainability and reduces duplicated code.

---

# Design Principles

Several software engineering principles guided the implementation.

## Separation of Responsibilities

Each module performs one specific task.

Examples:

- ingestion only collects data
- feature engineering only builds features
- training only trains models
- conformal prediction only calibrates intervals

This makes the code easier to debug, maintain, and extend.

---

## Reproducibility

Running

```bash
python src/automation/pipeline.py
```

reproduces the complete machine learning workflow from raw data ingestion through final prediction intervals.

No manual execution order is required.

---

## Automation

Rather than executing scripts manually, the pipeline orchestrates every stage automatically.

This reduces human error while ensuring that every execution follows the exact same workflow.

---

## Configuration over Hardcoding

Hyperparameters, regions, database credentials, and feature definitions are stored in a centralized configuration module.

Changing a parameter requires modification in only one location.

This approach improves readability while reducing maintenance effort.

---

# 4. Data Flow

The complete machine learning workflow begins with hourly electricity demand data retrieved from the U.S. Energy Information Administration (EIA) API and finishes with calibrated prediction intervals.

The complete execution flow is shown below.

```text
                EIA API
                   │
                   ▼
        ingest_EIA.py
                   │
                   ▼
      raw.electricity_demand
                   │
                   ▼
      build_features.sql
                   │
                   ▼
   features.demand_features
                   │
                   ▼
    train_quantiles.py
                   │
                   ▼
      LightGBM Models
                   │
                   ▼
  conformal_predict.py
                   │
                   ▼
 Prediction Intervals (.csv)
```

The pipeline is executed automatically through a single command.

```bash
python src/automation/pipeline.py
```

Internally, the automation module executes every stage in sequence.

1. Download the latest electricity demand data.
2. Store observations inside PostgreSQL.
3. Generate machine learning features.
4. Train quantile regression models.
5. Calibrate prediction intervals using conformal prediction.
6. Save trained models and prediction artifacts.

Every stage depends on the successful completion of the previous stage. If one stage fails, the pipeline immediately terminates to prevent downstream errors.

---

# 5. Database Design

GRIDTRUST stores raw observations inside PostgreSQL before any feature engineering or machine learning occurs.

The current database contains a raw schema.

```text
raw.electricity_demand
```

Current table structure:

```text
+----------------+-------------------------------+
| Column         | Description                   |
+----------------+-------------------------------+
| respondent     | Electricity market operator   |
| period         | Hourly timestamp              |
| value          | Electricity demand (MW)       |
+----------------+-------------------------------+
```

Example record:

```text
respondent : CISO

period     : 2024-06-15 13:00

value      : 28493
```

Each row represents a single hourly demand observation.

The combination of

```text
(respondent, period)
```

is defined as a UNIQUE constraint.

This prevents duplicate observations from being inserted during repeated pipeline executions.

The current project collects data from three electricity markets.

- CISO (California ISO)
- ERCO (ERCOT Texas)
- PJM (Pennsylvania-New Jersey-Maryland)

Partitioning data by respondent allows one feature engineering pipeline and one model training pipeline to be reused across multiple electricity markets.

---

# 6. Feature Engineering Pipeline

Raw electricity demand is not used directly for training.

Instead, the project constructs predictive features that capture historical demand patterns.

Feature engineering is performed entirely inside PostgreSQL using SQL window functions.

This approach provides several advantages.

- transformations remain reproducible
- computation occurs close to the data
- no duplicated preprocessing code exists in Python
- SQL execution scales efficiently for larger datasets

The current feature table contains the following variables.

| Feature     | Description             |
| ----------- | ----------------------- |
| demand      | Target variable         |
| lag_1h      | Demand one hour earlier |
| lag_24h     | Demand one day earlier  |
| lag_168h    | Demand one week earlier |
| hour_of_day | Hour of observation     |
| day_of_week | Day of week             |
| is_weekend  | Weekend indicator       |

The feature engineering workflow is illustrated below.

```text
Raw Demand

2024-06-15 10:00

↓

Lag Features

Previous Hour

↓

Previous Day

↓

Previous Week

↓

Calendar Features

Hour

Day

Weekend

↓

Model Ready Dataset
```

### Lag Features

Electricity demand exhibits strong temporal dependence.

Demand at the current hour is highly correlated with previous observations.

Three lag variables are included.

**lag_1h**

Captures immediate short-term dependence.

Useful for modelling rapid demand fluctuations.

---

**lag_24h**

Captures daily seasonality.

Electricity demand at 8 AM today is often similar to demand at 8 AM yesterday.

---

**lag_168h**

Captures weekly seasonality.

Demand on Monday morning is often similar to demand on the previous Monday morning.

---

### Calendar Features

Calendar variables provide additional context.

**hour_of_day**

Captures daily demand cycles caused by human activity.

---

**day_of_week**

Captures weekday versus weekday differences.

---

**is_weekend**

Provides a binary indicator for Saturdays and Sundays.

Electricity usage patterns typically differ between working days and weekends.

The resulting feature table becomes the input to all machine learning models.

---

# 7. Quantile Regression Pipeline

Traditional regression models predict a single value.

Example:

```text
Predicted Demand = 31,850 MW
```

While useful, this prediction provides no information about uncertainty.

GRIDTRUST instead predicts two independent values.

- Lower Quantile (5th percentile)
- Upper Quantile (95th percentile)

These predictions form an initial prediction interval.

```text
Lower Prediction ---------------- Upper Prediction

        29,800 MW         34,700 MW
```

The true demand is expected to fall inside this interval most of the time.

## Why Quantile Regression?

Electricity demand is influenced by many unpredictable factors including weather, holidays, outages, and human behavior.

Predicting a single value ignores this uncertainty.

Quantile regression estimates different points of the conditional demand distribution instead of only its average.

This allows the model to produce intervals rather than point estimates.

## Model Choice

GRIDTRUST uses LightGBM with the Quantile objective.

Two independent models are trained.

```text
                    Training Dataset
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
Lower Quantile Model              Upper Quantile Model
(alpha = 0.05)                    (alpha = 0.95)
          │                                 │
          └────────────────┬────────────────┘
                           ▼
                Initial Prediction Interval
```

Each model learns a different conditional quantile.

The lower model estimates conservative demand values.

The upper model estimates optimistic demand values.

Together they form the initial uncertainty interval.

---

## Time Series Split

Unlike standard machine learning datasets, time series observations cannot be randomly shuffled.

Random sampling would introduce future information into the training process and create unrealistic performance estimates.

GRIDTRUST preserves chronological order throughout the entire pipeline.

```text
Oldest
│
│──────────────────────────────────────────────────────────────Newest

|----------- Train -----------|------ Calibration ------|-- Test --|
```

Current split ratios are

- Training: 70%
- Calibration: 20%
- Testing: 10%

Each dataset serves a different purpose.

### Training Set

Used to train the two LightGBM quantile models.

---

### Calibration Set

Used exclusively by conformal prediction.

The calibration dataset is never used during model fitting.

Instead, it estimates how large prediction errors are in practice.

---

### Test Set

Used only for final evaluation.

This dataset simulates completely unseen future observations.

Keeping the test set untouched ensures that reported performance reflects realistic deployment conditions.

---

## Model Outputs

After training, the pipeline produces several artifacts.

```text
models/

    ciso/
        lower.pkl
        upper.pkl

    erco/
        lower.pkl
        upper.pkl

    pjm/
        lower.pkl
        upper.pkl
```

Additional datasets are also exported.

```text
outputs/

    calibration.csv

    test.csv
```

These datasets are later consumed by the conformal prediction stage.

---

# 8. Conformal Prediction Pipeline

While quantile regression produces prediction intervals, those intervals do not guarantee that the desired percentage of future observations will actually fall inside them.

For example, a model may attempt to produce a 90% prediction interval but achieve only 78% coverage on unseen data.

This creates a reliability problem.

A forecasting system should not only make predictions but should also provide uncertainty estimates that are statistically trustworthy.

GRIDTRUST addresses this problem using **Conformal Prediction**.

Conformal prediction is a model-agnostic calibration technique that adjusts prediction intervals using historical prediction errors.

Unlike retraining the machine learning model, conformal prediction acts as a calibration layer placed after model training.

The overall workflow is shown below.

```text
               LightGBM Quantile Models
                         │
                         ▼
          Initial Prediction Interval
                         │
                         ▼
             Calibration Dataset
                         │
                         ▼
          Compute Prediction Errors
                         │
                         ▼
             Calculate q_hat
                         │
                         ▼
          Expand Prediction Interval
                         │
                         ▼
      Final Conformal Prediction Interval
```

The machine learning model remains unchanged.

Only the prediction interval is adjusted.

---

## Why Calibration is Necessary

Even a well-trained model cannot perfectly estimate uncertainty.

Real-world demand is influenced by factors that may not exist in the training data.

Examples include

- sudden weather changes
- holidays
- unexpected outages
- abnormal consumer behaviour

As a result, prediction intervals are often too narrow.

Example:

```text
Lower Prediction

29,400 MW

Upper Prediction

31,800 MW

Actual Demand

33,100 MW
```

Although the point prediction may be reasonable, the interval completely misses the true observation.

Conformal prediction uses historical forecasting errors to determine how much these intervals should be widened.

---

## Nonconformity Scores

The first step is measuring how incorrect each calibration prediction is.

GRIDTRUST computes a nonconformity score for every observation in the calibration dataset.

The score represents the minimum expansion required for the prediction interval to include the true demand.

```text
Prediction Interval

|-----------|

Actual

        X

↓

Prediction Error

Distance from Interval
```

If the true demand already lies inside the prediction interval,

```text
Score = 0
```

Otherwise,

```text
Score > 0
```

Larger values indicate that the prediction interval was too narrow.

---

## Computing q_hat

After calculating nonconformity scores for every calibration observation, the scores are sorted.

```text
Calibration Scores

0

12

25

48

61

95

132

...

610

742

810
```

GRIDTRUST then selects the desired percentile of these errors.

This value is called

```text
q_hat
```

The value represents the maximum prediction error that should be tolerated in order to achieve the desired coverage level.

Higher values of q_hat produce wider prediction intervals.

Lower values produce narrower intervals.

---

## Applying Conformal Prediction

The calibrated interval is computed by expanding both sides of the original prediction interval.

```text
Original Interval

|----------------------|

↓

Expand by q_hat

<----- q_hat ----->

|------------------------------|

<----- q_hat ----->
```

Mathematically,

```text
Lower = Lower Prediction − q_hat

Upper = Upper Prediction + q_hat
```

No retraining is required.

Only the prediction interval is adjusted.

---

## Coverage

Coverage measures how often the true demand falls inside the prediction interval.

```text
Prediction Interval

|----------------------|

Actual

         X

Inside Interval

✓
```

Coverage is calculated as

```text
(Number of observations inside interval)

──────────────────────────────────────

(Total number of observations)
```

For example,

```text
900 observations inside interval

1000 total observations

Coverage = 90%
```

Higher coverage indicates more reliable uncertainty estimates.

---

## Coverage Gap

GRIDTRUST targets a coverage level of

```text
90%
```

Coverage Gap measures how far the observed coverage is from this target.

Example:

```text
Target Coverage

90%

Observed Coverage

84%

Coverage Gap

6%
```

A smaller coverage gap indicates better calibration.

An ideal conformal prediction system produces a coverage gap close to zero.

---

## Interval Width

Prediction intervals should be reliable without becoming unnecessarily large.

GRIDTRUST therefore measures the average interval width.

```text
Interval Width

Upper − Lower
```

Example:

```text
Lower

30,000 MW

Upper

35,000 MW

Width

5,000 MW
```

Very narrow intervals are informative but may miss many observations.

Very wide intervals capture almost everything but provide little practical value.

The objective is to balance

- high coverage
- narrow intervals

simultaneously.

---

## Pipeline Outputs

After conformal calibration, the pipeline generates

```text
outputs/

    ciso_conformal_predictions.csv

    erco_conformal_predictions.csv

    pjm_conformal_predictions.csv

    conformal_summary.csv
```

Each prediction file contains

- actual demand
- lower prediction
- upper prediction
- conformal lower bound
- conformal upper bound
- interval width
- inside interval indicator

The summary report contains

- q_hat
- empirical coverage
- coverage gap
- average interval width

These metrics provide a complete evaluation of prediction quality and uncertainty calibration.

---

## Why Conformal Prediction?

Traditional forecasting projects stop after producing predictions.

GRIDTRUST goes one step further by quantifying uncertainty and calibrating prediction intervals using historical forecasting errors.

This produces uncertainty estimates that are more reliable under real-world conditions without modifying the underlying machine learning models.

The combination of quantile regression and conformal prediction allows GRIDTRUST to generate forecasts that are not only accurate but also statistically interpretable.

# 9. Automation Pipeline

Executing multiple scripts manually is both time-consuming and error-prone.

To ensure every stage executes in the correct order, GRIDTRUST uses a centralized automation pipeline.

The pipeline is responsible for orchestrating the complete machine learning workflow.

Current execution flow:

```text
pipeline.py
      │
      ▼
Data Ingestion
      │
      ▼
Feature Engineering
      │
      ▼
Quantile Model Training
      │
      ▼
Conformal Prediction
      │
      ▼
Pipeline Complete
```

The automation layer uses Python's `subprocess` module to execute each stage as an independent process.

Each pipeline stage is treated as an isolated component.

This provides several advantages.

- Individual stages can be tested independently.
- Failures are isolated to a single module.
- The execution order remains consistent.
- Additional stages can be added without modifying existing modules.

The pipeline records the execution time of every stage and immediately terminates if any step fails.

Example execution log:

```text
GRIDTRUST PIPELINE STARTED

↓

Data Ingestion

↓

Feature Engineering

↓

Quantile Model Training

↓

Conformal Prediction

↓

GRIDTRUST PIPELINE FINISHED
```

This approach improves reproducibility while providing a single entry point for the complete project.

---

# 10. Configuration Management

Rather than scattering constants throughout multiple scripts, GRIDTRUST centralizes all configurable values inside a single configuration module.

```text
src/

    config.py
```

The configuration file stores

- API credentials
- Database connection string
- Electricity market regions
- Machine learning features
- Train/Calibration/Test split ratios
- Quantile values
- Model hyperparameters

Example:

```python
TRAIN_RATIO = 0.70

CALIBRATION_RATIO = 0.20

TEST_RATIO = 0.10
```

Instead of hardcoding values repeatedly throughout the project,

```python
TRAIN_RATIO
```

is imported wherever required.

This provides several benefits.

- Single source of truth
- Easier maintenance
- Consistent configuration across modules
- Simpler experimentation

Changing a parameter requires modifying only one file.

---

# 11. Logging and Error Handling

GRIDTRUST uses Python's logging module to record pipeline execution.

Unlike print statements, logging provides structured execution information including

- execution timestamps
- severity levels
- pipeline stage
- execution duration

Example output

```text
2026-07-31 00:07:05

INFO

Starting: Data Ingestion
```

Each pipeline stage is monitored independently.

If a stage fails,

```text
Data Ingestion

↓

Feature Engineering

↓

Model Training

↓

ERROR

Pipeline Stops
```

subsequent stages are never executed.

This prevents partially completed pipelines from producing inconsistent outputs.

The automation pipeline also measures execution time for every stage.

Example:

```text
Feature Engineering

Completed Successfully

3.52 seconds
```

Runtime measurements help identify performance bottlenecks as the project grows.

---

# 12. Project Outputs

Every successful pipeline execution generates several artifacts.

## Trained Models

```text
models/

    ciso_lower.pkl

    ciso_upper.pkl

    erco_lower.pkl

    erco_upper.pkl

    pjm_lower.pkl

    pjm_upper.pkl
```

These serialized LightGBM models can later be loaded for inference without retraining.

---

## Prediction Files

```text
outputs/

    ciso_predictions.csv

    ciso_conformal_predictions.csv

    erco_predictions.csv

    erco_conformal_predictions.csv

    pjm_predictions.csv

    pjm_conformal_predictions.csv
```

These files contain

- predicted demand
- calibrated intervals
- interval width
- coverage indicator

---

## Evaluation Reports

Additional summary files are produced after every execution.

Examples include

```text
conformal_summary.csv

feature_importance.csv

test.csv

calibration.csv
```

These artifacts make it possible to evaluate model performance without rerunning the training pipeline.

---

# 13. Current Limitations

Although GRIDTRUST provides statistically calibrated prediction intervals, several limitations remain.

Current limitations include

- Fixed LightGBM hyperparameters.
- Limited feature set based primarily on historical demand.
- No external weather or holiday information.
- Manual pipeline execution.
- No continuous monitoring after deployment.

These limitations provide opportunities for future improvements.

---

# 14. Future Improvements

Several enhancements are planned for future versions of GRIDTRUST.

## Data Validation

Introduce automated data quality checks before feature engineering.

Example checks include

- duplicate timestamps
- missing hours
- null values
- negative demand
- chronological ordering

Pipelines should fail immediately when invalid data is detected.

---

## Continuous Integration

Automatically execute tests whenever new code is pushed to GitHub.

This ensures that future changes do not accidentally break the project.

---

## Scheduled Retraining

Instead of manually running the pipeline,

the workflow can be executed automatically using a scheduler such as

- Windows Task Scheduler
- Cron
- GitHub Actions
- Apache Airflow

---

## Docker Deployment

The project already includes a Docker configuration.

Containerization allows GRIDTRUST to run consistently across different operating systems without requiring manual dependency installation.

---

## Monitoring

Future versions could monitor

- prediction coverage
- interval width
- model drift
- data drift

Alerts could be generated whenever performance falls below acceptable thresholds.

---

# Conclusion

GRIDTRUST demonstrates a complete end-to-end machine learning workflow for uncertainty-aware electricity demand forecasting.

The project combines database engineering, feature engineering, machine learning, uncertainty quantification, automation, and software engineering into a reproducible production-style pipeline.

Rather than producing only point forecasts, GRIDTRUST generates calibrated prediction intervals that quantify forecasting uncertainty, making predictions more reliable and interpretable for real-world decision making.

The modular architecture also provides a strong foundation for future enhancements including automated validation, continuous integration, deployment, and monitoring.
