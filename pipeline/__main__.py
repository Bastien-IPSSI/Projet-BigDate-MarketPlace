"""Point d'entrée : python -m pipeline <commande>.

    check                                        vérifie la connexion à Postgres, MinIO et l'API
    extract --date 2026-04-07                    récupère les commandes d'un jour (test du client API)
    run --date 2026-04-07                        pipeline complet pour une date
    refresh-dims                                 recharge vendeurs et produits dans les dimensions
    backfill --start 2026-08-22 --end 2026-10-20 run sur chaque date de la période
    replay --date 2026-04-07                     rejoue une date depuis MinIO, sans appeler l'API
"""
import argparse
import logging
import os
import sys
from datetime import date, timedelta

import requests

from pipeline import db, raw
from pipeline.aggregate import aggregate
from pipeline.extract import extract_dims, extract_orders
from pipeline.load import load_dims, load_orders
from pipeline.transform import transform_dims, transform_orders

log = logging.getLogger("pipeline")


def check() -> int:
    ok = True

    try:
        with db.connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name IN ('staging', 'dwh', 'analytics') ORDER BY 1"
            )
            print(f"[OK] Postgres, schémas : {[r[0] for r in cur.fetchall()]}")
    except Exception as e:
        ok = False
        print(f"[KO] Postgres : {e}")

    try:
        raw.s3_client().head_bucket(Bucket=os.environ["MINIO_BUCKET"])
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


def refresh_dims(conn):
    sellers, products = extract_dims()
    load_dims(conn, sellers, products)
    transform_dims(conn)
    log.info("Dimensions : %d vendeurs, %d produits", len(sellers), len(products))


def process(conn, day, orders):
    """Étapes communes à run et replay : staging -> dwh -> analytics."""
    n = load_orders(conn, day, orders)
    log.info("[%s] load      : %d lignes dans staging.orders", day, n)
    transform_orders(conn, day)
    log.info("[%s] transform : dwh.fact_orders mis à jour", day)
    aggregate(conn, day)
    log.info("[%s] aggregate : tables analytics mises à jour", day)


def run(conn, day):
    # Les clés étrangères imposent des dimensions remplies avant les commandes
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM dwh.dim_seller)")
        dims_empty = not cur.fetchone()[0]
    if dims_empty:
        log.info("Dimensions vides : lancement de refresh-dims")
        refresh_dims(conn)

    orders = extract_orders(day)
    log.info("[%s] extract   : %d lignes reçues de l'API", day, len(orders))
    log.info("[%s] raw       : %s", day, raw.write_raw(day, orders))
    process(conn, day, orders)


def replay(conn, day):
    orders = raw.read_raw(day)
    log.info("[%s] replay    : %d lignes relues depuis MinIO (%s)", day, len(orders), raw.raw_key(day))
    process(conn, day, orders)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Vérifie la connexion à Postgres, MinIO et l'API")
    sub.add_parser("refresh-dims", help="Recharge vendeurs et produits dans les dimensions")
    for name in ("extract", "run", "replay"):
        sub.add_parser(name).add_argument("--date", type=date.fromisoformat, required=True)
    p = sub.add_parser("backfill", help="Lance run sur chaque date de la période (bornes incluses)")
    p.add_argument("--start", type=date.fromisoformat, required=True)
    p.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()

    if args.command == "check":
        return check()
    if args.command == "extract":
        orders = extract_orders(args.date)
        print(f"Commandes du {args.date} : {len(orders)} lignes")
        print(f"Exemple : {orders[0]}")
        return 0

    conn = db.connect()
    try:
        if args.command == "refresh-dims":
            refresh_dims(conn)
        elif args.command == "run":
            run(conn, args.date)
        elif args.command == "replay":
            replay(conn, args.date)
        elif args.command == "backfill":
            day = args.start
            while day <= args.end:
                run(conn, day)
                day += timedelta(days=1)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
