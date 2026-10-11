-- Separate preaggregations prevent revenue/request fanout.
WITH eligible AS (SELECT * FROM users WHERE observed_days >= 30),
revenue AS (
    SELECT u.user_id, COALESCE(SUM(p.amount_usd), 0) AS revenue
    FROM eligible u LEFT JOIN payments p ON p.user_id = u.user_id
      AND p.timestamp >= u.signup_date AND p.timestamp < datetime(u.signup_date, '+30 days')
    GROUP BY u.user_id
), costs AS (
    SELECT u.user_id, COALESCE(SUM(d.inference_cost), 0) AS inference_cost,
           MAX(COALESCE(d.is_active, 0)) AS active,
           COALESCE(SUM(d.requests), 0) AS requests
    FROM eligible u LEFT JOIN user_days d ON d.user_id = u.user_id AND d.age_day < 30
    GROUP BY u.user_id
), totals AS (
    SELECT u.experiment_group AS variant, COUNT(*) AS users,
           SUM(r.revenue) AS revenue, SUM(c.inference_cost) AS inference_cost,
           SUM(c.active) AS active_users, SUM(c.requests) AS requests
    FROM eligible u JOIN revenue r USING(user_id) JOIN costs c USING(user_id)
    GROUP BY u.experiment_group
)
SELECT *, revenue - inference_cost AS contribution,
       (revenue - inference_cost) / NULLIF(revenue, 0) AS margin,
       1.0 * inference_cost / NULLIF(users, 0) AS cost_per_user,
       1.0 * inference_cost / NULLIF(active_users, 0) AS cost_per_active_user,
       1.0 * revenue / NULLIF(inference_cost, 0) AS revenue_to_inference_ratio,
       1.0 * requests / NULLIF(users, 0) AS requests_per_user
FROM totals ORDER BY variant;
