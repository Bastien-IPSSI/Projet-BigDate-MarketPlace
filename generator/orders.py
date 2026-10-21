"""Génération des lignes de commande d'une journée, déterministe par date."""
import hashlib
import random
from datetime import date, datetime, timedelta
from functools import lru_cache
from itertools import accumulate

import numpy as np

from generator import config as c
from generator.reference import build_reference


def date_seed(day: date) -> int:
    return int(hashlib.md5(day.isoformat().encode()).hexdigest(), 16) % 2**32


def event_factor(day: date) -> tuple[float, str | None]:
    """Facteur de volume lié aux événements de anomalies.json (Black Friday, soldes, chutes)."""
    iso = day.isoformat()
    a = c.ANOMALIES
    if iso in a["revenue_drops"]["dates"]:
        return a["revenue_drops"]["dates"][iso], "revenue_drop"
    if iso in a["black_friday"]["dates"]:
        return a["black_friday"]["factor"], "black_friday"
    for start, end in a["soldes"]["periods"]:
        if start <= iso <= end:
            return a["soldes"]["factor"], "soldes"
    return 1.0, None


def expected_orders(day: date) -> float:
    trend = 1 + c.TREND_PER_DAY * (day - c.TREND_REFERENCE).days
    return c.BASE_DAILY_ORDERS * c.WEEKDAY_FACTOR[day.weekday()] * trend * event_factor(day)[0]


def on_break(seller_id: str, day: date) -> bool:
    """Le temps est découpé en périodes de 14 jours ; sur chacune, un vendeur a 10 % de chances
    d'être en pause. La graine (vendeur, période) rend le tirage identique pour tous les jours de la période.
    Les périodes sont décalées d'un vendeur à l'autre pour que les pauses ne commencent pas toutes le même jour."""
    offset = int(seller_id[1:]) % c.PAUSE_DAYS
    period = (day.toordinal() + offset) // c.PAUSE_DAYS
    return random.Random(f"{seller_id}-{period}").random() < c.PAUSE_RATE


def _pick(rng, choices_probs):
    choices, probs = choices_probs
    return rng.choices(choices, weights=probs)[0]


@lru_cache(maxsize=8)
def generate_day(day: date, quality_defects: bool = c.QUALITY_DEFECTS) -> tuple[list[dict], dict]:
    """Renvoie (lignes de commande, pièges injectés) pour une date.

    Les tirages des défauts qualité sont toujours effectués, même désactivés :
    la suite des tirages ne change pas, donc les autres données restent identiques.
    """
    if not (c.ORDERS_START <= day <= c.ORDERS_END):
        raise ValueError(f"date hors période {c.ORDERS_START} → {c.ORDERS_END}")
    ref = build_reference()
    rng = random.Random(date_seed(day))

    # Vendeurs pouvant vendre ce jour : actifs, déjà arrivés sur la plateforme et pas en pause
    eligible = [i for i, s in enumerate(ref.sellers)
                if s["is_active"] and s["joined_date"] <= day.isoformat() and not on_break(s["seller_id"], day)]
    seller_cum_weights = list(accumulate(ref.seller_weights[i] for i in eligible))

    traps = {"date": day.isoformat(), "event": event_factor(day)[1],
             "suspicious_prices": [], "null_customer": [], "future_created_at": [], "duplicated_order_ids": []}
    midnight = datetime(day.year, day.month, day.day)
    # numpy uniquement pour la loi de Poisson (absente du module random)
    n_orders = int(np.random.default_rng(date_seed(day)).poisson(expected_orders(day)))
    # Heures triées : les numéros de commande suivent l'ordre chronologique
    seconds = sorted(rng.choices(range(24), weights=c.HOUR_WEIGHTS)[0] * 3600 + rng.randrange(3600)
                     for _ in range(n_orders))
    lines = []

    for o in range(n_orders):
        order_id = f"ORD-{day:%Y%m%d}-{o + 1:06d}"
        created_at = midnight + timedelta(seconds=seconds[o])
        customer = rng.choice(ref.customers)["customer_id"]
        status = _pick(rng, c.STATUS)
        payment = _pick(rng, c.PAYMENT_METHOD)
        order_lines = []

        for k in range(_pick(rng, c.LINES_PER_ORDER)):
            s = rng.choices(eligible, cum_weights=seller_cum_weights)[0]
            product = ref.products[rng.choice(ref.seller_products[s])]
            quantity = _pick(rng, c.QUANTITY)
            unit_price = round(product["base_price"] * (1 + rng.uniform(-c.PRICE_NOISE, c.PRICE_NOISE)), 2)
            line = {
                "order_id": order_id,
                "order_line_id": f"{order_id}-{k + 1}",
                "created_at": created_at.isoformat(),
                "customer_id": customer,
                "seller_id": ref.sellers[s]["seller_id"],
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": None,  # calculé une fois le prix définitif connu
                "status": status,
                "payment_method": payment,
            }

            # Prix suspect (toujours actif) : 0,01 € ou 10x le prix habituel
            if rng.random() < c.SUSPICIOUS_PRICE_RATE:
                too_low = rng.random() < 0.5
                line["unit_price"] = 0.01 if too_low else round(product["base_price"] * 10, 2)
                traps["suspicious_prices"].append({
                    "order_line_id": line["order_line_id"], "product_id": product["product_id"],
                    "base_price": product["base_price"], "unit_price": line["unit_price"],
                    "kind": "too_low" if too_low else "too_high",
                })

            # Défauts qualité : tirés dans tous les cas, appliqués seulement si activés
            null_customer = rng.random() < c.DEFECT_NULL_CUSTOMER_RATE
            future_date = rng.random() < c.DEFECT_FUTURE_DATE_RATE
            future_shift = rng.randint(365, 3 * 365)
            if quality_defects and null_customer:
                line["customer_id"] = None
                traps["null_customer"].append(line["order_line_id"])
            if quality_defects and future_date:
                line["created_at"] = (created_at + timedelta(days=future_shift)).isoformat()
                traps["future_created_at"].append(line["order_line_id"])

            line["total_amount"] = round(line["quantity"] * line["unit_price"], 2)
            order_lines.append(line)

        lines.extend(order_lines)
        # Doublon : la commande entière est réémise à l'identique
        if rng.random() < c.DEFECT_DUPLICATE_ORDER_RATE and quality_defects:
            lines.extend(dict(l) for l in order_lines)
            traps["duplicated_order_ids"].append(order_id)

    return lines, traps


def generate_orders(day: date) -> list[dict]:
    return generate_day(day)[0]
