"""Extraction depuis l'API."""
from pipeline.client import MarketplaceAPIClient


def extract_orders(day):
    return MarketplaceAPIClient().get_orders(day)


def extract_dims():
    client = MarketplaceAPIClient()
    return client.get_sellers(), client.get_products()
