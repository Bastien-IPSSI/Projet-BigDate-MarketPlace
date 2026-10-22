"""Connexion à Postgres et exécution des fichiers SQL du dossier sql/."""
import os
from pathlib import Path

import psycopg2

SQL_DIR = Path(__file__).parent.parent / "sql"


def connect():
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=5432,
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def run_sql_file(conn, filename, params=None):
    """Exécute un fichier SQL dans une seule transaction (tout ou rien).

    Les paramètres sont passés à psycopg2 (%(dt)s dans le fichier), jamais
    insérés dans la chaîne SQL à la main.
    """
    sql = (SQL_DIR / filename).read_text(encoding="utf-8")
    with conn, conn.cursor() as cur:  # commit si tout passe, rollback sinon
        cur.execute(sql, params)
