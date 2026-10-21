"""Point d'entrée : python -m pipeline <commande>.

Premier commit : seule la commande `check` existe (vérifie la connexion aux services).
Les commandes run / backfill / refresh-dims / replay seront développées ultérieurement.
"""
import argparse
import os
import sys

import boto3
import psycopg2
import requests


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


def main() -> int:
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Vérifie la connexion à Postgres, MinIO et l'API")
    args = parser.parse_args()

    if args.command == "check":
        return check()
    return 1


if __name__ == "__main__":
    sys.exit(main())
