-- Finance : commissions encaissées par jour sur les 60 jours précédant « le jour » (visualisation « Histogramme »)
-- {{date}} : variable Metabase de type Date, facultative (vide = dernière date chargée).
WITH ref AS (
    SELECT max(dt) AS d
    FROM analytics.daily_summary
    WHERE true [[AND dt <= {{date}}]]
)
SELECT dt AS "Date", commission_total AS "Commissions"
FROM analytics.daily_summary, ref
WHERE dt > ref.d - 60 AND dt <= ref.d
ORDER BY dt;
