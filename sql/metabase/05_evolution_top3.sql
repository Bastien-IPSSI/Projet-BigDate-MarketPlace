-- Top Sellers : CA quotidien des 3 meilleurs vendeurs d'un mois (visualisation « Ligne »)
-- {{mois}} : filtre de champ Metabase relié à analytics.daily_summary.dt, widget « Mois et année ».
--   - vide       : le mois de la dernière date chargée
--   - renseigné  : le mois choisi
WITH ref AS (
    SELECT date_trunc('month', max(dt)) AS mois
    FROM analytics.daily_summary
    WHERE true [[AND {{mois}}]]
),
top3 AS (
    SELECT seller_id
    FROM analytics.seller_daily
    JOIN ref ON date_trunc('month', dt) = ref.mois
    GROUP BY seller_id
    ORDER BY SUM(revenue) DESC
    LIMIT 3
)
SELECT sd.dt AS "Date", s.name AS "Vendeur", sd.revenue AS "CA"
FROM analytics.seller_daily sd
JOIN top3 USING (seller_id)
JOIN dwh.dim_seller s ON s.seller_id = sd.seller_id
JOIN ref ON date_trunc('month', sd.dt) = ref.mois
ORDER BY sd.dt;
