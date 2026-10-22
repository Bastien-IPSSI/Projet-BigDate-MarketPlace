-- staging.orders -> dwh.fact_orders pour la journée passée en paramètre
-- Exécuté dans une seule transaction : DELETE + INSERT => idempotent.

DELETE FROM dwh.fact_orders WHERE dt = %(dt)s;

INSERT INTO dwh.fact_orders (order_line_id, order_id, dt, created_at, seller_id, product_id, customer_id,
                             quantity, unit_price, total_amount, commission_amount, status, payment_method)
-- DISTINCT ON : une seule ligne par order_line_id (supprime les commandes dupliquées par l'API)
SELECT DISTINCT ON (order_line_id)
       order_line_id, order_id, dt, created_at, seller_id, product_id, customer_id,
       quantity, unit_price, total_amount,
       -- Commission : 0.12 x montant, uniquement sur les lignes payées
       CASE WHEN status = 'paid' THEN ROUND(total_amount * 0.12, 2) ELSE 0 END,
       status, payment_method
FROM staging.orders
WHERE dt = %(dt)s
ORDER BY order_line_id;
