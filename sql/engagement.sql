-- DAU/WAU/MAU are distinct user counts in trailing calendar windows.
WITH calendar AS (SELECT DISTINCT date FROM user_days),
variants(variant) AS (VALUES ('control'), ('treatment')),
active AS (
    SELECT d.date, d.user_id, u.experiment_group AS variant
    FROM user_days d JOIN users u USING(user_id) WHERE d.is_active = 1
), counts AS (
    SELECT c.date, v.variant,
           COUNT(DISTINCT CASE WHEN a.date = c.date THEN a.user_id END) AS dau,
           COUNT(DISTINCT CASE WHEN a.date >= date(c.date, '-6 days') THEN a.user_id END) AS wau,
           COUNT(DISTINCT a.user_id) AS mau
    FROM calendar c CROSS JOIN variants v
    LEFT JOIN active a ON a.variant = v.variant AND a.date BETWEEN date(c.date, '-29 days') AND c.date
    GROUP BY c.date, v.variant
)
SELECT *, 1.0 * dau / NULLIF(mau, 0) AS stickiness FROM counts ORDER BY date, variant;
