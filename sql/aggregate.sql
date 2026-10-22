-- dwh -> analytics pour la journée passée en paramètre, uniquement les lignes payées.
-- Exécuté dans une seule transaction : DELETE + INSERT => idempotent.

-- CA et nombre de commandes par vendeur
DELETE FROM analytics.seller_daily WHERE dt = %(dt)s;
INSERT INTO analytics.seller_daily (dt, seller_id, revenue, nb_orders)
SELECT dt, seller_id, SUM(total_amount), COUNT(DISTINCT order_id)
FROM dwh.fact_orders
WHERE dt = %(dt)s AND status = 'paid'
GROUP BY dt, seller_id;

-- CA par catégorie
DELETE FROM analytics.category_daily WHERE dt = %(dt)s;
INSERT INTO analytics.category_daily (dt, category, revenue)
SELECT f.dt, p.category, SUM(f.total_amount)
FROM dwh.fact_orders f
JOIN dwh.dim_product p ON p.product_id = f.product_id
WHERE f.dt = %(dt)s AND f.status = 'paid'
GROUP BY f.dt, p.category;

-- Synthèse du jour (le top vendeur vient de seller_daily, calculé juste au-dessus)
DELETE FROM analytics.daily_summary WHERE dt = %(dt)s;
INSERT INTO analytics.daily_summary (dt, nb_orders, revenue, avg_basket, commission_total, top_seller_id)
SELECT dt,
       COUNT(DISTINCT order_id),
       SUM(total_amount),
       ROUND(SUM(total_amount) / COUNT(DISTINCT order_id), 2),
       SUM(commission_amount),
       (SELECT seller_id FROM analytics.seller_daily WHERE dt = %(dt)s ORDER BY revenue DESC LIMIT 1)
FROM dwh.fact_orders
WHERE dt = %(dt)s AND status = 'paid'
GROUP BY dt;
