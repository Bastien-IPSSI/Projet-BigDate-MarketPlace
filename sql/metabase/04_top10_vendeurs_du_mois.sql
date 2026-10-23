-- Top Sellers : top 10 des vendeurs sur un mois (visualisation « Histogramme » ou « Rangées »)
-- {{mois}} : filtre de champ Metabase relié à analytics.daily_summary.dt, widget « Mois et année ».
--   - vide       : le mois de la dernière date chargée
--   - renseigné  : le mois choisi
WITH ref AS (
    SELECT date_trunc('month', max(dt)) AS mois
    FROM analytics.daily_summary
    WHERE true [[AND {{mois}}]]
)
SELECT s.name AS "Vendeur", SUM(sd.revenue) AS "CA du mois", SUM(sd.nb_orders) AS "Commandes"
FROM analytics.seller_daily sd
JOIN dwh.dim_seller s ON s.seller_id = sd.seller_id
JOIN ref ON date_trunc('month', sd.dt) = ref.mois
GROUP BY s.name
ORDER BY 2 DESC
LIMIT 10;
