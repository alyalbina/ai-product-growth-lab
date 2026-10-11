-- Bounded rolling return: any active age in [checkpoint, 30], inclusive.
-- Same fully observed 31-day denominator at every checkpoint. No immortal tail.
WITH checkpoints(age_day) AS (VALUES (1), (7), (14), (30)),
variants(variant) AS (VALUES ('control'), ('treatment')),
outcomes AS (
    SELECT u.user_id, u.experiment_group AS variant, c.age_day,
           MAX(COALESCE(d.is_active, 0)) AS returned
    FROM users u CROSS JOIN checkpoints c
    LEFT JOIN user_days d ON d.user_id = u.user_id AND d.age_day BETWEEN c.age_day AND 30
    WHERE u.observed_days > 30
    GROUP BY u.user_id, u.experiment_group, c.age_day
)
SELECT v.variant, c.age_day, COUNT(o.user_id) AS eligible,
       1.0 * COALESCE(SUM(o.returned), 0) / NULLIF(COUNT(o.user_id), 0) AS rate
FROM variants v CROSS JOIN checkpoints c
LEFT JOIN outcomes o ON o.variant = v.variant AND o.age_day = c.age_day
GROUP BY v.variant, c.age_day ORDER BY v.variant, c.age_day;
