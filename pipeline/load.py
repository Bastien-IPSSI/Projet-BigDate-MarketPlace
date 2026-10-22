"""Chargement dans le schéma staging."""
from psycopg2.extras import execute_values

ORDER_COLUMNS = ["order_id", "order_line_id", "created_at", "customer_id", "seller_id", "product_id",
                 "quantity", "unit_price", "total_amount", "status", "payment_method"]


def load_orders(conn, day, orders):
    """Remplace les commandes de la journée dans staging.orders.

    DELETE puis INSERT dans la même transaction : relancer la même date
    donne exactement le même résultat (idempotence).
    """
    rows = [[o[c] for c in ORDER_COLUMNS] + [day] for o in orders]
    with conn, conn.cursor() as cur:
        cur.execute("DELETE FROM staging.orders WHERE dt = %s", (day,))
        execute_values(cur, f"INSERT INTO staging.orders ({', '.join(ORDER_COLUMNS)}, dt) VALUES %s", rows)
    return len(rows)


def load_dims(conn, sellers, products):
    """Remplace entièrement staging.sellers et staging.products."""
    with conn, conn.cursor() as cur:
        cur.execute("TRUNCATE staging.sellers, staging.products")
        execute_values(
            cur,
            "INSERT INTO staging.sellers (seller_id, name, type, country, city, joined_date, is_active) VALUES %s",
            [[s["seller_id"], s["name"], s["type"], s["country"], s["city"], s["joined_date"], s["is_active"]]
             for s in sellers],
        )
        execute_values(
            cur,
            "INSERT INTO staging.products (product_id, name, category, seller_id, base_price, created_at) VALUES %s",
            [[p["product_id"], p["name"], p["category"], p["seller_id"], p["base_price"], p["created_at"]]
             for p in products],
        )
