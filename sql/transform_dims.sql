-- staging.sellers / staging.products -> dimensions (SCD1 : on écrase les attributs)
-- ON CONFLICT DO UPDATE : insère les nouveaux, met à jour les existants.
-- Les vendeurs d'abord : dim_product a une clé étrangère vers dim_seller.

INSERT INTO dwh.dim_seller (seller_id, name, type, country, city, joined_date, is_active)
SELECT seller_id, name, type, country, city, joined_date, is_active
FROM staging.sellers
ON CONFLICT (seller_id) DO UPDATE SET
    name        = EXCLUDED.name,
    type        = EXCLUDED.type,
    country     = EXCLUDED.country,
    city        = EXCLUDED.city,
    joined_date = EXCLUDED.joined_date,
    is_active   = EXCLUDED.is_active;

INSERT INTO dwh.dim_product (product_id, name, category, seller_id, base_price)
SELECT product_id, name, category, seller_id, base_price
FROM staging.products
ON CONFLICT (product_id) DO UPDATE SET
    name       = EXCLUDED.name,
    category   = EXCLUDED.category,
    seller_id  = EXCLUDED.seller_id,
    base_price = EXCLUDED.base_price;
