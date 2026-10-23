-- Executive Summary : CA quotidien sur les 30 jours précédant « le jour » (visualisation « Ligne »)
-- {{date}} : variable Metabase de type Date, facultative (vide = dernière date chargée).
WITH ref AS (
    SELECT max(dt) AS d
    FROM analytics.daily_summary
    WHERE true [[AND dt <= {{date}}]]
)
SELECT dt AS "Date", revenue AS "CA"
FROM analytics.daily_summary, ref
WHERE dt > ref.d - 30 AND dt <= ref.d
ORDER BY dt;
