-- Schéma du DWH MarketPlace Analytics
-- Exécuté automatiquement par Postgres au premier démarrage (volume vide).
-- Rejouable à la main sans risque (IF NOT EXISTS / ON CONFLICT DO NOTHING).
--
-- Trois couches :
--   staging   : données brutes de l'API, typées, sans transformation
--   dwh       : modèle en étoile (dimensions + table de faits)
--   analytics : agrégats prêts pour les dashboards

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE SCHEMA IF NOT EXISTS analytics;


-- =====================================================================
-- STAGING : copie fidèle de l'API (doublons et défauts compris)
-- =====================================================================

-- Pas de clé primaire : on garde les doublons reçus pour pouvoir les mesurer.
-- customer_id est nullable : les lignes défectueuses doivent pouvoir être chargées.
CREATE TABLE IF NOT EXISTS staging.orders (
    order_id        TEXT          NOT NULL,
    order_line_id   TEXT          NOT NULL,
    created_at      TIMESTAMP     NOT NULL,
    customer_id     TEXT,
    seller_id       TEXT          NOT NULL,
    product_id      TEXT          NOT NULL,
    quantity        INTEGER       NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL,
    total_amount    NUMERIC(12,2) NOT NULL,
    status          TEXT          NOT NULL,
    payment_method  TEXT          NOT NULL,
    dt              DATE          NOT NULL,              -- date demandée à l'API (--date)
    loaded_at       TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_staging_orders_dt ON staging.orders (dt);

CREATE TABLE IF NOT EXISTS staging.sellers (
    seller_id    TEXT        PRIMARY KEY,
    name         TEXT        NOT NULL,
    type         TEXT        NOT NULL,
    country      TEXT        NOT NULL,
    city         TEXT        NOT NULL,
    joined_date  DATE        NOT NULL,
    is_active    BOOLEAN     NOT NULL,
    loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.products (
    product_id  TEXT          PRIMARY KEY,
    name        TEXT          NOT NULL,
    category    TEXT          NOT NULL,
    seller_id   TEXT          NOT NULL,
    base_price  NUMERIC(10,2) NOT NULL,
    created_at  DATE          NOT NULL,
    loaded_at   TIMESTAMPTZ   NOT NULL DEFAULT now()
);


-- =====================================================================
-- DWH : modèle en étoile
-- =====================================================================

-- Calendrier, pré-rempli sur 2025-2027
CREATE TABLE IF NOT EXISTS dwh.dim_date (
    dt           DATE     PRIMARY KEY,
    year         SMALLINT NOT NULL,
    quarter      SMALLINT NOT NULL,
    month        SMALLINT NOT NULL,
    week         SMALLINT NOT NULL,   -- semaine ISO
    day_of_week  SMALLINT NOT NULL,   -- 1 = lundi ... 7 = dimanche (ISO)
    is_weekend   BOOLEAN  NOT NULL
);

INSERT INTO dwh.dim_date (dt, year, quarter, month, week, day_of_week, is_weekend)
SELECT d::date,
       EXTRACT(YEAR    FROM d),
       EXTRACT(QUARTER FROM d),
       EXTRACT(MONTH   FROM d),
       EXTRACT(WEEK    FROM d),
       EXTRACT(ISODOW  FROM d),
       EXTRACT(ISODOW  FROM d) IN (6, 7)
FROM generate_series('2025-01-01'::date, '2027-12-31'::date, interval '1 day') AS d
ON CONFLICT (dt) DO NOTHING;

-- Dimensions SCD1 : on écrase les attributs à chaque refresh (pas d'historique)
CREATE TABLE IF NOT EXISTS dwh.dim_seller (
    seller_id    TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL,
    type         TEXT    NOT NULL,
    country      TEXT    NOT NULL,
    city         TEXT    NOT NULL,
    joined_date  DATE    NOT NULL,
    is_active    BOOLEAN NOT NULL
);

-- La catégorie reste dénormalisée ici (pas de dim_category)
CREATE TABLE IF NOT EXISTS dwh.dim_product (
    product_id  TEXT          PRIMARY KEY,
    name        TEXT          NOT NULL,
    category    TEXT          NOT NULL,
    seller_id   TEXT          NOT NULL REFERENCES dwh.dim_seller (seller_id),
    base_price  NUMERIC(10,2) NOT NULL
);

-- Grain : une ligne de commande.
-- Les commandes cancelled et refunded sont conservées (traçabilité) mais exclues
-- du CA : toutes les tables analytics filtrent sur status = 'paid'.
-- La commission (12 %) n'est due que sur les lignes payées, 0 sinon.
CREATE TABLE IF NOT EXISTS dwh.fact_orders (
    order_line_id      TEXT          PRIMARY KEY,
    order_id           TEXT          NOT NULL,
    dt                 DATE          NOT NULL REFERENCES dwh.dim_date (dt),
    created_at         TIMESTAMP     NOT NULL,
    seller_id          TEXT          NOT NULL REFERENCES dwh.dim_seller (seller_id),
    product_id         TEXT          NOT NULL REFERENCES dwh.dim_product (product_id),
    customer_id        TEXT,                     -- nullable : défauts qualité tolérés (phase 5)
    quantity           INTEGER       NOT NULL,
    unit_price         NUMERIC(10,2) NOT NULL,
    total_amount       NUMERIC(12,2) NOT NULL,
    commission_amount  NUMERIC(12,2) NOT NULL,
    status             TEXT          NOT NULL CHECK (status IN ('paid', 'cancelled', 'refunded')),
    payment_method     TEXT          NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fact_orders_dt ON dwh.fact_orders (dt);


-- =====================================================================
-- ANALYTICS : agrégats quotidiens (uniquement les lignes paid)
-- =====================================================================

CREATE TABLE IF NOT EXISTS analytics.daily_summary (
    dt                DATE          PRIMARY KEY,
    nb_orders         INTEGER       NOT NULL,
    revenue           NUMERIC(14,2) NOT NULL,
    avg_basket        NUMERIC(10,2) NOT NULL,   -- revenue / nb_orders
    commission_total  NUMERIC(14,2) NOT NULL,
    top_seller_id     TEXT                      -- vendeur au plus gros CA du jour
);

CREATE TABLE IF NOT EXISTS analytics.seller_daily (
    dt         DATE          NOT NULL,
    seller_id  TEXT          NOT NULL,
    revenue    NUMERIC(14,2) NOT NULL,
    nb_orders  INTEGER       NOT NULL,
    PRIMARY KEY (dt, seller_id)
);

CREATE TABLE IF NOT EXISTS analytics.category_daily (
    dt        DATE          NOT NULL,
    category  TEXT          NOT NULL,
    revenue   NUMERIC(14,2) NOT NULL,
    PRIMARY KEY (dt, category)
);
