-- Session identifiers are distinct within user, not assumed globally unique.
WITH eligible AS (SELECT * FROM users WHERE observed_days >= 30),
user_sessions AS (
    SELECT u.user_id, u.experiment_group AS variant, COUNT(DISTINCT e.session_id) AS sessions
    FROM eligible u LEFT JOIN events e ON e.user_id = u.user_id
      AND e.event_timestamp >= u.signup_date AND e.event_timestamp < datetime(u.signup_date, '+30 days')
    GROUP BY u.user_id, u.experiment_group
), user_requests AS (
    SELECT u.user_id, COUNT(r.request_id) AS requests
    FROM eligible u LEFT JOIN ai_requests r ON r.user_id = u.user_id AND r.success = 1
      AND r.timestamp >= u.signup_date AND r.timestamp < datetime(u.signup_date, '+30 days')
    GROUP BY u.user_id
)
SELECT s.variant, COUNT(*) AS eligible_users, AVG(s.sessions) AS sessions_per_user,
       AVG(r.requests) AS requests_per_user
FROM user_sessions s JOIN user_requests r USING(user_id) GROUP BY s.variant;
