"""Référentiel (vendeurs, produits, clients), généré une seule fois à partir d'une graine fixe."""
import math
import random
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache

from faker import Faker

from generator import config as c


@dataclass
class Reference:
    sellers: list[dict]
    products: list[dict]
    customers: list[dict]
    seller_weights: list[float]       # poids de Zipf (interne, non exposé par l'API)
    seller_products: list[list[int]]  # index des produits de chaque vendeur


def _random_date(rng, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _pick(rng, choices_probs):
    choices, probs = choices_probs
    return rng.choices(choices, weights=probs)[0]


def _ascii(s: str) -> str:
    """'Céline Dupré' -> 'celinedupre' (pour les emails)."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().replace(" ", "")


@lru_cache(maxsize=1)
def build_reference() -> Reference:
    rng = random.Random(c.GLOBAL_SEED)
    fake = Faker("fr_FR")
    fake.seed_instance(c.GLOBAL_SEED)

    # --- Vendeurs ---
    companies = set()
    while len(companies) < c.N_SELLERS:
        companies.add(fake.company())
    sellers = []
    for i, name in enumerate(sorted(companies)):
        country = _pick(rng, c.COUNTRIES)
        sellers.append({
            "seller_id": f"S{i + 1:05d}",
            "name": name,
            "type": _pick(rng, c.SELLER_TYPES),
            "country": country,
            "city": rng.choice(c.CITIES[country]),
            "joined_date": _random_date(rng, c.SELLERS_JOIN_START, c.SELLERS_JOIN_END).isoformat(),
            "is_active": rng.random() >= c.INACTIVE_SELLER_RATE,
        })
    # Loi de Zipf : le vendeur de rang r pèse 1 / r^exposant (rang tiré au hasard)
    ranks = list(range(1, c.N_SELLERS + 1))
    rng.shuffle(ranks)
    seller_weights = [1 / r ** c.ZIPF_EXPONENT for r in ranks]

    # --- Produits : un par vendeur (chacun peut vendre), le reste réparti au hasard ---
    categories = list(c.CATEGORIES)
    cat_probs = [c.CATEGORIES[k]["weight"] for k in categories]
    owners = list(range(c.N_SELLERS)) + [rng.randrange(c.N_SELLERS) for _ in range(c.N_PRODUCTS - c.N_SELLERS)]
    products, seller_products = [], [[] for _ in range(c.N_SELLERS)]
    for j, s in enumerate(owners):
        cat = rng.choices(categories, weights=cat_probs)[0]
        params = c.CATEGORIES[cat]
        # Prix log-normal : beaucoup de produits abordables, une longue traîne de produits chers
        price = max(1.0, rng.lognormvariate(math.log(params["median"]), params["sigma"]))
        products.append({
            "product_id": f"P{j + 1:06d}",
            "name": f"{rng.choice(params['nouns'])} {rng.choice(c.COLORS)}",
            "category": cat,
            "seller_id": sellers[s]["seller_id"],
            "base_price": round(price, 2),
            "created_at": sellers[s]["joined_date"],
        })
        seller_products[s].append(j)

    # --- Clients : pools de prénoms/noms Faker (appeler Faker 200 000 fois serait lent) ---
    first_names = [fake.first_name() for _ in range(600)]
    last_names = [fake.last_name() for _ in range(600)]
    customers = []
    for i in range(c.N_CUSTOMERS):
        first, last = rng.choice(first_names), rng.choice(last_names)
        customers.append({
            "customer_id": f"C{i + 1:06d}",
            "name": f"{first} {last}",
            "email": f"{_ascii(first)}.{_ascii(last)}{i + 1}@{rng.choice(c.EMAIL_DOMAINS)}",
            "city": rng.choice(c.CITIES["FR"]),
            "signup_date": _random_date(rng, c.CUSTOMERS_SIGNUP_START, c.CUSTOMERS_SIGNUP_END).isoformat(),
        })

    return Reference(sellers, products, customers, seller_weights, seller_products)
