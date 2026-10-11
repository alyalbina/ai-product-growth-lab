-- 30-day ITT funnel: successful request -> meaningful use -> later-day repeat.
-- Paid conversion is marginal ITT, not conditional on activation or repetition.
-- repeat_then_paid additionally requires first payment after the exact repeat time.
WITH eligible AS (SELECT * FROM users WHERE observed_days >= 30),
successful_requests AS (
    SELECT r.request_id, r.user_id, r.timestamp,
           ROW_NUMBER() OVER (
               PARTITION BY r.user_id, date(r.timestamp)
               ORDER BY r.timestamp, r.request_id
           ) AS success_order
    FROM ai_requests r JOIN eligible u ON u.user_id = r.user_id
    WHERE r.success = 1 AND r.timestamp >= u.signup_date
      AND r.timestamp < datetime(u.signup_date, '+30 days')
),
first_request AS (
    SELECT u.user_id, MIN(r.timestamp) AS first_at
    FROM eligible u LEFT JOIN successful_requests r USING(user_id)
    GROUP BY u.user_id
), meaningful_days AS (
    -- A meaningful day's achievement occurs when its second success completes.
    SELECT user_id, timestamp AS meaningful_at
    FROM successful_requests WHERE success_order = 2
), activated AS (
    SELECT u.user_id, MIN(m.meaningful_at) AS activated_at
    FROM eligible u LEFT JOIN meaningful_days m USING(user_id)
    GROUP BY u.user_id
), repeated AS (
    SELECT a.user_id, MIN(m.meaningful_at) AS repeat_at
    FROM activated a LEFT JOIN meaningful_days m ON m.user_id = a.user_id
      AND date(m.meaningful_at) > date(a.activated_at)
    GROUP BY a.user_id
), paid AS (
    SELECT u.user_id, MIN(p.timestamp) AS paid_at
    FROM eligible u LEFT JOIN payments p ON p.user_id = u.user_id AND p.amount_usd > 0
      AND p.timestamp >= u.signup_date AND p.timestamp < datetime(u.signup_date, '+30 days')
    GROUP BY u.user_id
)
SELECT u.experiment_group AS variant, u.acquisition_channel, COUNT(*) AS registered,
       SUM(f.first_at IS NOT NULL) AS first_request,
       SUM(f.first_at IS NOT NULL AND a.activated_at IS NOT NULL) AS activated,
       SUM(f.first_at IS NOT NULL AND r.repeat_at IS NOT NULL) AS repeat_usage,
       SUM(p.paid_at IS NOT NULL) AS paid_users,
       1.0 * SUM(p.paid_at IS NOT NULL) / NULLIF(COUNT(*), 0) AS free_to_paid_conversion,
       SUM(r.repeat_at IS NOT NULL AND p.paid_at >= r.repeat_at) AS repeat_then_paid
FROM eligible u JOIN first_request f USING(user_id) JOIN activated a USING(user_id)
JOIN repeated r USING(user_id) JOIN paid p USING(user_id)
GROUP BY u.experiment_group, u.acquisition_channel;
