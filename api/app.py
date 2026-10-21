"""API Flask qui sert les données du générateur.

Routes (Bearer token obligatoire sauf /health) :
    GET /health
    GET /orders?date=YYYY-MM-DD&page=1&page_size=5000
    GET /sellers?page=&page_size=      (limit = alias de page_size)
    GET /products?page=&page_size=
    GET /customers?page=&page_size=

Simulation d'instabilité (variables d'environnement) :
    API_ERROR_RATE      probabilité de répondre 503 (ex. 0.05)
    API_MAX_LATENCY_MS  latence aléatoire ajoutée, entre 0 et cette valeur
"""
import logging
import math
import os
import random
import time
from datetime import date
from functools import wraps

from flask import Flask, abort, jsonify, request

from generator.orders import generate_orders
from generator.reference import build_reference

API_TOKEN = os.environ["API_TOKEN"]
API_ERROR_RATE = float(os.getenv("API_ERROR_RATE", "0"))
API_MAX_LATENCY_MS = int(os.getenv("API_MAX_LATENCY_MS", "0"))
DEFAULT_PAGE_SIZE = 5000
MAX_PAGE_SIZE = 20000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = Flask(__name__)
app.json.sort_keys = False
build_reference()  # chargé au démarrage (partagé entre workers grâce à gunicorn --preload)


def protected(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if request.headers.get("Authorization") != f"Bearer {API_TOKEN}":
            return jsonify(error="unauthorized"), 401
        if API_MAX_LATENCY_MS:
            time.sleep(random.uniform(0, API_MAX_LATENCY_MS) / 1000)
        if random.random() < API_ERROR_RATE:
            app.logger.warning("Erreur simulée sur %s", request.full_path)
            return jsonify(error="simulated failure"), 503
        return view(*args, **kwargs)
    return wrapper


def paginate(total: int, fetch) -> dict:
    """fetch(start, stop) renvoie les lignes de la page demandée."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", request.args.get("limit", DEFAULT_PAGE_SIZE)))
    except ValueError:
        abort(400, "page et page_size doivent être des entiers")
    if page < 1 or not 1 <= page_size <= MAX_PAGE_SIZE:
        abort(400, f"page >= 1 et 1 <= page_size <= {MAX_PAGE_SIZE}")
    start = (page - 1) * page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)),
        "data": fetch(start, min(start + page_size, total)),
    }


@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=e.description), 400


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/orders")
@protected
def orders():
    try:
        day = date.fromisoformat(request.args["date"])
        lines = generate_orders(day)
    except KeyError:
        abort(400, "paramètre date obligatoire (YYYY-MM-DD)")
    except ValueError as e:
        abort(400, str(e))
    return jsonify(date=day.isoformat(), **paginate(len(lines), lambda a, b: lines[a:b]))


@app.get("/sellers")
@protected
def sellers():
    data = build_reference().sellers
    return jsonify(paginate(len(data), lambda a, b: data[a:b]))


@app.get("/products")
@protected
def products():
    data = build_reference().products
    return jsonify(paginate(len(data), lambda a, b: data[a:b]))


@app.get("/customers")
@protected
def customers():
    data = build_reference().customers
    return jsonify(paginate(len(data), lambda a, b: data[a:b]))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
