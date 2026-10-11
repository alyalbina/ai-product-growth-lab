-- Descriptive association, not a causal estimate: no randomized grant timing.
-- Next-calendar-day windows; grants without a fully observed next day are excluded.
WITH observation_end AS (
    SELECT user_id, datetime(signup_date, '+' || observed_days || ' days') AS end_at FROM users
), grants AS (
    SELECT t.transaction_id, t.user_id, t.timestamp,
           LEAD(t.timestamp) OVER (PARTITION BY t.user_id ORDER BY t.timestamp) AS next_grant
    FROM token_transactions t WHERE t.transaction_type = 'grant'
), eligible AS (
    SELECT g.* FROM grants g JOIN observation_end o USING(user_id)
    WHERE datetime(date(g.timestamp), '+2 days') <= o.end_at
), outcomes AS (
    SELECT g.transaction_id, u.experiment_group AS variant,
           MAX(CASE WHEN d.is_active = 1 THEN 1 ELSE 0 END) AS active_next_calendar_day,
           MAX(CASE WHEN g.next_grant < datetime(date(g.timestamp), '+2 days') THEN 1 ELSE 0 END) AS overlapping_grant
    FROM eligible g JOIN users u USING(user_id)
    LEFT JOIN user_days d ON d.user_id = g.user_id AND date(d.date) = date(g.timestamp, '+1 day')
    GROUP BY g.transaction_id, u.experiment_group
)
SELECT variant, COUNT(*) AS observed_grants,
       AVG(active_next_calendar_day) AS next_calendar_day_active_share,
       SUM(overlapping_grant) AS grants_with_overlapping_reward_window
FROM outcomes GROUP BY variant;
