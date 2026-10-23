-- Top Sellers : vendeurs sans vente depuis plus de 7 jours au « jour » (visualisation « Tableau »)
-- {{date}} : variable Metabase de type Date, facultative (vide = dernière date chargée).
-- Seuls les vendeurs ayant déjà vendu sur la période chargée apparaissent.
WITH ref AS (
    SELECT max(dt) AS d
    FROM analytics.daily_summary
    WHERE true [[AND dt <= {{date}}]]
)
SELECT s.name AS "Vendeur",
       MAX(sd.dt) AS "Dernière vente",
       ref.d - MAX(sd.dt) AS "Jours sans vente"
FROM analytics.seller_daily sd
JOIN dwh.dim_seller s ON s.seller_id = sd.seller_id
CROSS JOIN ref
WHERE sd.dt <= ref.d
GROUP BY s.name, ref.d
HAVING MAX(sd.dt) < ref.d - 7
ORDER BY 3 DESC;
