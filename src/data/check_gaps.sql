-- =============================================================
-- check_gaps.sql
-- Purpose: Detect missing hourly electricity demand observations
--          in the raw EIA-930 regional demand data.
--
-- Dataset: raw.electricity_demand
-- Regions: CISO, ERCO, PJM
--
-- Why:    Time-series forecasting requires a continuous hourly
--         timeline. Missing timestamps can make LAG-based features
--         misleading, since the previous available row may not
--         represent the previous actual hour.
--
-- Author: Ayesha Amer
-- =============================================================



WITH expected_hours AS (
    SELECT generate_series(
        -- getting the min hour (for series starting point)
        (SELECT MIN(period) FROM raw.electricity_demand WHERE respondent = 'CISO'),
        -- getting the max hour (for series ending point)
        (SELECT MAX(period) FROM raw.electricity_demand WHERE respondent = 'CISO'),
        INTERVAL '1 hour'
    ) AS period
)
SELECT e.period AS missing_period 
FROM expected_hours e LEFT JOIN raw.electricity_demand r
ON e.period = r.period AND respondent = 'CISO'
WHERE r.period IS NULL
ORDER BY e.period;
