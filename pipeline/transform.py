"""Staging -> dwh (modèle en étoile)."""
from pipeline.db import run_sql_file


def transform_orders(conn, day):
    run_sql_file(conn, "transform_fact_orders.sql", {"dt": day})


def transform_dims(conn):
    run_sql_file(conn, "transform_dims.sql")
