-- =============================================================
-- build_features.sql
-- Purpose: Transform raw hourly electricity demand into a
--          model-ready feature table.
--
-- Features:
--   - lag_1h:   previous hour's demand
--   - lag_24h:  demand at the same hour on the previous day
--   - lag_168h: demand at the same hour on the previous week
--   - hour_of_day: captures daily demand patterns
--   - day_of_week: captures weekly demand patterns
--   - is_weekend: identifies weekend behavior
--
-- Source:  raw.electricity_demand
-- Output:  features.demand_features
-- Author:  Ayesha Amer
-- =============================================================

CREATE SCHEMA IF NOT EXISTS features;

DROP TABLE IF EXISTS features.demand_features;

CREATE TABLE features.demand_features AS
SELECT respondent, period, value as demand,

        -- demand an hour ago, a day ago and a week ago
        LAG(value,1) OVER (PARTITION BY respondent ORDER BY period) AS lag_1h,
        LAG(value,24) OVER (PARTITION BY respondent ORDER BY period) AS lag_24h,
        LAG(value,168) OVER (PARTITION BY respondent ORDER BY period) AS lag_168h,

        -- hour of the day
        EXTRACT(HOUR FROM period) as hour_of_day,

        -- day of the week
        EXTRACT(DOW FROM period) as day_of_week,

        -- binary weekend flag
        CASE WHEN EXTRACT(DOW FROM period) IN (0,6) Then 1 ELSE 0 END AS is_weekend
    
    FROM raw.electricity_demand
    ORDER BY respondent, period;

