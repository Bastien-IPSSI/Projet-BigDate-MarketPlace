# MarketPlace Analytics

Pipeline ELT de bout en bout pour une marketplace simulée : API → data lake (MinIO) → staging → DWH en étoile (Postgres) → tables analytics → dashboards Metabase.

> README en cours de rédaction : il est complété à chaque phase du projet.

## Arborescence

```
generator/          simulation des données (déterministe par date)
api/                API Flask qui sert les données générées
pipeline/           client API, extract, load, transform, CLI
init-db/schema.sql  schémas staging / dwh / analytics (exécuté au 1er démarrage)
sql/                transformations dwh + analytics
docker-compose.yml
.env.example
```

## Services Docker

| Service           | Rôle                                   | Port(s) hôte                  |
|-------------------|----------------------------------------|-------------------------------|
| `postgres-dwh`    | Entrepôt de données                    | 5432                          |
| `minio`           | Data lake S3 (raw layer)               | 9000 (API), 9001 (console)    |
| `minio-init`      | Crée le bucket `data-lake` puis s'arrête | —                           |
| `api-marketplace` | API Flask du générateur                | 5000                          |
| `metabase`        | Dashboards                             | 3000                          |
| `pipeline`        | CLI ELT, lancé à la demande (profil `tools`) | —                       |

Volumes nommés : `pg-dwh-data`, `minio-data`, `metabase-data`.

> MinIO : les images officielles `minio/minio` ne sont plus publiées sur Docker Hub ni quay.io. On utilise `pgsty/minio`, un fork communautaire qui reprend le même binaire (même API S3, même console, `mc` inclus).

## Lancement

Prérequis : Docker Desktop (Compose v2).

```bash
# 1. Configuration
cp .env.example .env          # PowerShell : Copy-Item .env.example .env

# 2. Démarrer la stack
docker compose up -d --build
docker compose ps             # tous les services doivent être "healthy"

# 3. Vérifier que le pipeline joint Postgres, MinIO et l'API
docker compose run --rm pipeline check
```

Interfaces :
- Console MinIO : http://localhost:9001 (identifiants `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` du `.env`)
- Metabase : http://localhost:3000
- API : http://localhost:5000/health

## Commandes utiles

| Action | Commande |
|--------|----------|
| Démarrer la stack | `docker compose up -d --build` |
| Arrêter la stack | `docker compose down` |
| Tout réinitialiser (supprime les données) | `docker compose down -v` |
| Logs d'un service | `docker compose logs -f api-marketplace` |
| Lancer une commande du pipeline | `docker compose run --rm pipeline <commande>` |
| Rejouer `init-db/schema.sql` | `docker compose down -v` puis `up` (le script ne s'exécute que sur un volume vide) |

Le code de `pipeline/` et `sql/` est monté dans le conteneur : pas besoin de rebuild après une modification. Un rebuild (`docker compose build pipeline`) n'est nécessaire que si `pipeline/requirements.txt` change.
| Statistiques d'une journée générée | `docker compose exec api-marketplace python -m generator sample --date 2026-04-07` |
| Exporter les lignes piégées | `docker compose exec api-marketplace python -m generator traps --start 2026-08-22 --end 2026-10-20` |

Le code de `generator/` et `api/` est aussi monté dans le conteneur de l'API : après une modification, `docker compose restart api-marketplace` suffit.

## Générateur de données

Toutes les données sont **déterministes** : une même date produit toujours exactement les mêmes commandes, ce qui permet de prouver l'idempotence du pipeline.

- Référentiel : graine globale fixe (`GLOBAL_SEED`), généré une fois au démarrage de l'API.
- Commandes : graine `int(md5(date).hexdigest(), 16) % 2**32`. Les tirages des défauts qualité sont toujours effectués : les désactiver ne change pas le reste des données.

Les paramètres sont dans [generator/config.py](generator/config.py). Explication détaillée : [docs/phase1-generateur-api.md](docs/phase1-generateur-api.md).

### Référentiel

| Entité | Volume | Réalisme |
|--------|--------|----------|
| Vendeurs | 2 400 | Types artisan / DNVB / revendeur ; 85 % FR, puis BE, CH, ES ; arrivées étalées de 2023 à 2026 ; 5 % désactivés |
| Catégories | 10 | Mode, Maison, Beauté, High-tech, Épicerie fine, Sport, Jouets, Bijoux, Livres & Papeterie, Animalerie, avec des poids de ventes différents |
| Produits | 18 000 (`CATALOG_SIZE`, 180 000 possible) | Catégorie tirée selon les poids des catégories ; prix log-normal par catégorie ; au moins un produit par vendeur |
| Clients | 200 000 | Noms Faker fr_FR, emails sur des domaines réservés `example.*`, inscriptions de 2021 à 2027 |

### Commandes (une date de 2025-01-01 à 2027-12-31)

- Volume : loi de Poisson autour de 8 500 commandes, avec une saisonnalité hebdomadaire (dimanche et lundi +15 %, mardi -10 %) et une tendance linéaire de +0,1 %/jour (base au 2026-01-01). Black Friday ×3, soldes ×1,3.
- 1 à 4 lignes par commande (environ 1,35 en moyenne). Quantité égale à 1 dans 90 % des cas.
- Vendeur : loi de Zipf (poids = 1 / rang), si bien que 20 % des vendeurs font environ 80 % du CA. Un vendeur ne vend qu'à partir de sa date d'arrivée. Sur chaque période de 14 jours, il a 10 % de chances d'être en pause, ce qui alimente le tableau « vendeurs inactifs ».
- Produit tiré parmi ceux du vendeur. Prix = base_price × (1 ± 5 %).
- Statut : paid 92 %, cancelled 5 %, refunded 3 %. Paiement : card, paypal, apple_pay, bank_transfer, gift_card.

### Anomalies injectées

| Anomalie | Taux | Désactivable |
|----------|------|--------------|
| Chutes de CA (50 à 60 % du volume normal) | dates listées dans [generator/anomalies.json](generator/anomalies.json) | non |
| Prix suspects : 0,01 € ou 10 × base_price | 0,1 % des lignes | non |
| `customer_id` null | 0,2 % des lignes | `QUALITY_DEFECTS=false` |
| `created_at` dans le futur (+1 à +3 ans) | 0,1 % des lignes | `QUALITY_DEFECTS=false` |
| Commande entière dupliquée (même `order_id` et `order_line_id`) | 0,1 % des commandes | `QUALITY_DEFECTS=false` |

Les dates piégées sont dans `generator/anomalies.json`. Les lignes piégées d'une période sont exportées dans `generator/traps.json` avec `python -m generator traps`. Ce fichier sert de vérité terrain pour vérifier la data quality et la détection d'anomalies.

## API Marketplace

Authentification `Authorization: Bearer <API_TOKEN>` sur toutes les routes sauf `/health`. Sans token ou avec un token invalide, l'API répond 401.

| Route | Paramètres |
|-------|-----------|
| `GET /health` | — |
| `GET /orders` | `date` (obligatoire), `page`, `page_size` |
| `GET /sellers` | `page`, `page_size` (ou `limit`) |
| `GET /products` | `page`, `page_size` |
| `GET /customers` | `page`, `page_size` (ou `limit`) |

Réponse paginée : `{"page", "page_size", "total", "total_pages", "data": [...]}`. Par défaut `page_size` vaut 5 000, au maximum 20 000.

Pour simuler une API instable et tester le retry du client, définir dans le `.env` (puis `docker compose up -d api-marketplace`) :
- `API_ERROR_RATE=0.05` : 5 % des appels répondent 503 ;
- `API_MAX_LATENCY_MS=2000` : ajoute une latence aléatoire de 0 à 2 s.

## Modèle de données

Trois schémas Postgres, définis dans [init-db/schema.sql](init-db/schema.sql) :

- `staging` : copie brute de l'API (doublons et défauts compris) ;
- `dwh` : modèle en étoile, avec `fact_orders` (grain : une ligne de commande) et les dimensions `dim_date`, `dim_seller`, `dim_product` ;
- `analytics` : agrégats quotidiens `daily_summary`, `seller_daily`, `category_daily`.

Les commandes `cancelled` et `refunded` sont conservées dans `fact_orders` mais exclues du CA (`status = 'paid'`), et leur commission vaut 0.
