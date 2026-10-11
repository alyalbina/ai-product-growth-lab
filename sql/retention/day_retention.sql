-- Exact-day retention. Assignment denominator includes users with no events.
-- observed_days is number of observed ages starting at zero.
WITH checkpoints(age_day) AS (VALUES (1), (7), (30)),
variants(variant) AS (VALUES ('control'), ('treatment')),
eligible AS (
    SELECT u.user_id, u.experiment_group AS variant, c.age_day
    FROM users u CROSS JOIN checkpoints c
    WHERE u.observed_days > c.age_day
), returned AS (
    SELECT user_id, age_day, MAX(is_active) AS retained,
           MAX(is_meaningful) AS meaningful_retained
    FROM user_days GROUP BY user_id, age_day
)
SELECT v.variant, c.age_day, COUNT(e.user_id) AS eligible,
       COALESCE(SUM(r.retained), 0) AS retained,
       1.0 * COALESCE(SUM(r.retained), 0) / NULLIF(COUNT(e.user_id), 0) AS rate,
       1.0 * COALESCE(SUM(r.meaningful_retained), 0) / NULLIF(COUNT(e.user_id), 0) AS meaningful_rate
FROM variants v CROSS JOIN checkpoints c
LEFT JOIN eligible e ON e.variant = v.variant AND e.age_day = c.age_day
LEFT JOIN returned r ON r.user_id = e.user_id AND r.age_day = e.age_day
GROUP BY v.variant, c.age_day ORDER BY v.variant, c.age_day;
