"""Client de l'API Marketplace."""
import logging
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class MarketplaceAPIClient:
    def __init__(self):
        # URL et token lus dans le .env, jamais écrits dans le code
        self.base_url = os.environ["API_URL"]
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {os.environ['API_TOKEN']}"

        # Retry automatique sur les timeouts et les erreurs 5xx : 5 tentatives,
        # attentes de 0, 2, 4 puis 8 s. Les erreurs 4xx ne sont pas retentées.
        retry = Retry(total=4, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def _get_all(self, path, params=None):
        """Parcourt toutes les pages de l'API et renvoie la liste complète des lignes."""
        params = dict(params or {}, page=1)
        rows = []
        while True:
            response = self.session.get(self.base_url + path, params=params, timeout=30)
            response.raise_for_status()  # erreur 4xx : exception immédiate
            body = response.json()
            rows.extend(body["data"])
            logger.info("GET %s page %d/%d", path, body["page"], body["total_pages"])
            if body["page"] >= body["total_pages"]:
                return rows
            params["page"] += 1

    def get_orders(self, day):
        return self._get_all("/orders", {"date": str(day)})

    def get_sellers(self):
        return self._get_all("/sellers")

    def get_products(self):
        return self._get_all("/products")

    def get_customers(self):
        return self._get_all("/customers")
