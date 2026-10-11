-- Signup-month cohorts. Each checkpoint excludes only immature users.
WITH checkpoints(age_day) AS (VALUES (1), (7), (14), (30)),
cohorts AS (
    SELECT DISTINCT strftime('%Y-%m', signup_date) AS cohort, experiment_group AS variant FROM users
), eligible AS (
    SELECT u.user_id, strftime('%Y-%m', u.signup_date) AS cohort,
           u.experiment_group AS variant, c.age_day
    FROM users u CROSS JOIN checkpoints c WHERE u.observed_days > c.age_day
)
SELECT co.cohort, co.variant, c.age_day, COUNT(e.user_id) AS eligible,
       1.0 * COALESCE(SUM(d.is_active), 0) / NULLIF(COUNT(e.user_id), 0) AS rate
FROM cohorts co CROSS JOIN checkpoints c
LEFT JOIN eligible e ON e.cohort = co.cohort AND e.variant = co.variant AND e.age_day = c.age_day
LEFT JOIN user_days d ON d.user_id = e.user_id AND d.age_day = e.age_day
GROUP BY co.cohort, co.variant, c.age_day ORDER BY co.cohort, co.variant, c.age_day;
