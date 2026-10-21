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
