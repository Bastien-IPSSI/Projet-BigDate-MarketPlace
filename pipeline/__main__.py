"""Point d'entrée : python -m pipeline <commande>.

    check                     vérifie la connexion à Postgres, MinIO et l'API
    extract --date 2026-04-07 récupère les commandes d'un jour via le client API

Les commandes run / backfill / refresh-dims / replay seront développées ultérieurement.
"""
import argparse
import logging
import os
import sys
from datetime import date

import boto3
import psycopg2
import requests

from pipeline.client import MarketplaceAPIClient


def check() -> int:
    ok = True

    try:
        with psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            port=5432,
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        ) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name IN ('staging', 'dwh', 'analytics') ORDER BY 1"
            )
            print(f"[OK] Postgres, schémas : {[r[0] for r in cur.fetchall()]}")
    except Exception as e:
        ok = False
        print(f"[KO] Postgres : {e}")

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ROOT_USER"],
            aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        )
        s3.head_bucket(Bucket=os.environ["MINIO_BUCKET"])
        print(f"[OK] MinIO, bucket : {os.environ['MINIO_BUCKET']}")
    except Exception as e:
        ok = False
        print(f"[KO] MinIO : {e}")

    try:
        r = requests.get(f"{os.environ['API_URL']}/health", timeout=5)
        r.raise_for_status()
        print(f"[OK] API : {r.json()}")
    except Exception as e:
        ok = False
        print(f"[KO] API : {e}")

    return 0 if ok else 1


def extract(day: date) -> int:
    orders = MarketplaceAPIClient().get_orders(day)
    print(f"Commandes du {day} : {len(orders)} lignes")
    print(f"Exemple : {orders[0]}")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Vérifie la connexion à Postgres, MinIO et l'API")
    p = sub.add_parser("extract", help="Récupère les commandes d'un jour (test du client API)")
    p.add_argument("--date", type=date.fromisoformat, required=True)
    args = parser.parse_args()

    if args.command == "check":
        return check()
    if args.command == "extract":
        return extract(args.date)
    return 1


if __name__ == "__main__":
    sys.exit(main())
