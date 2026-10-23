-- Executive Summary : top 5 des vendeurs du jour (visualisation « Histogramme » ou « Rangées »)
-- {{date}} : variable Metabase de type Date, facultative (vide = dernière date chargée).
WITH ref AS (
    SELECT max(dt) AS d
    FROM analytics.daily_summary
    WHERE true [[AND dt <= {{date}}]]
)
SELECT s.name AS "Vendeur", sd.revenue AS "CA", sd.nb_orders AS "Commandes"
FROM analytics.seller_daily sd
JOIN dwh.dim_seller s ON s.seller_id = sd.seller_id
JOIN ref ON sd.dt = ref.d
ORDER BY sd.revenue DESC
LIMIT 5;
