-- Finance : cumul des commissions depuis le début de chaque mois, sur 60 jours (visualisation « Aire »)
-- {{date}} : variable Metabase de type Date, facultative (vide = dernière date chargée).
-- SUM(...) OVER : somme cumulée qui repart de zéro à chaque nouveau mois. Elle est calculée
-- sur toutes les dates (sous-requête c), puis on ne garde que les 60 jours affichés.
WITH ref AS (
    SELECT max(dt) AS d
    FROM analytics.daily_summary
    WHERE true [[AND dt <= {{date}}]]
)
SELECT c.dt AS "Date", c.cumul AS "Cumul du mois"
FROM (
    SELECT dt, SUM(commission_total) OVER (PARTITION BY date_trunc('month', dt) ORDER BY dt) AS cumul
    FROM analytics.daily_summary
) c, ref
WHERE c.dt > ref.d - 60 AND c.dt <= ref.d
ORDER BY c.dt;
