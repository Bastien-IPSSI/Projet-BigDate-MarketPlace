"""dwh -> analytics (agrégats quotidiens)."""
from pipeline.db import run_sql_file


def aggregate(conn, day):
    run_sql_file(conn, "aggregate.sql", {"dt": day})
