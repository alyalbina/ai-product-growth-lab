-- Cash collections, not plan prices. Each eligible user gets identical 30-day exposure.
WITH eligible AS (SELECT * FROM users WHERE observed_days >= 30),
user_revenue AS (
    SELECT u.user_id, u.signup_date, u.experiment_group,
           COALESCE(SUM(p.amount_usd), 0.0) AS revenue
    FROM eligible u LEFT JOIN payments p ON p.user_id = u.user_id
      AND p.timestamp >= u.signup_date AND p.timestamp < datetime(u.signup_date, '+30 days')
    GROUP BY u.user_id, u.signup_date, u.experiment_group
)
SELECT strftime('%Y-%m', signup_date) AS cohort, experiment_group AS variant,
       COUNT(*) AS eligible_users, SUM(revenue > 0) AS paying_users,
       SUM(revenue) AS revenue, AVG(revenue) AS arpu,
       SUM(revenue) / NULLIF(SUM(revenue > 0), 0) AS arppu,
       1.0 * SUM(revenue > 0) / NULLIF(COUNT(*), 0) AS paid_conversion
FROM user_revenue GROUP BY cohort, variant ORDER BY cohort, variant;
