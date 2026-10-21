"""Paramètres du générateur de données simulées."""
import json
import os
from datetime import date
from pathlib import Path

# --- Graines et volumes ---
GLOBAL_SEED = 2026
N_SELLERS = 2_400
N_PRODUCTS = int(os.getenv("CATALOG_SIZE", "18000"))
N_CUSTOMERS = 200_000
QUALITY_DEFECTS = os.getenv("QUALITY_DEFECTS", "true").lower() in ("1", "true", "yes")

# --- Période couverte ---
SELLERS_JOIN_START, SELLERS_JOIN_END = date(2023, 1, 1), date(2026, 12, 31)
CUSTOMERS_SIGNUP_START, CUSTOMERS_SIGNUP_END = date(2021, 1, 1), date(2027, 6, 30)
ORDERS_START, ORDERS_END = date(2025, 1, 1), date(2027, 12, 31)

# --- Volume de commandes ---
BASE_DAILY_ORDERS = 8_500
TREND_REFERENCE = date(2026, 1, 1)   # facteur de tendance = 1 à cette date
TREND_PER_DAY = 0.001                # +0,1 %/jour (linéaire)
WEEKDAY_FACTOR = {0: 1.15, 1: 0.90, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.15}  # lundi = 0

# Lois discrètes : (valeurs, probabilités)
LINES_PER_ORDER = ([1, 2, 3, 4], [0.75, 0.18, 0.05, 0.02])
QUANTITY = ([1, 2, 3, 4, 5], [0.90, 0.06, 0.025, 0.01, 0.005])
STATUS = (["paid", "cancelled", "refunded"], [0.92, 0.05, 0.03])
PAYMENT_METHOD = (
    ["card", "paypal", "apple_pay", "bank_transfer", "gift_card"],
    [0.65, 0.20, 0.08, 0.04, 0.03],
)
PRICE_NOISE = 0.05
# Répartition horaire des commandes (0h → 23h)
HOUR_WEIGHTS = [1, 0.5, 0.3, 0.2, 0.2, 0.3, 0.8, 1.5, 2.5, 3, 3.5, 4,
                5, 5, 4, 3.5, 3.5, 4, 4.5, 5, 6, 6, 4.5, 2.5]

# --- Vendeurs ---
ZIPF_EXPONENT = 1.0          # ~20 % des vendeurs font ~80 % du CA
INACTIVE_SELLER_RATE = 0.05  # vendeurs désactivés, ne vendent jamais
PAUSE_RATE = 0.10            # chance d'être en pause sur une période de PAUSE_DAYS jours
PAUSE_DAYS = 14
SELLER_TYPES = (["artisan", "DNVB", "revendeur"], [0.45, 0.20, 0.35])
COUNTRIES = (["FR", "BE", "CH", "ES"], [0.85, 0.07, 0.04, 0.04])
CITIES = {
    "FR": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Montpellier", "Strasbourg",
           "Bordeaux", "Lille", "Rennes", "Reims", "Toulon", "Saint-Étienne", "Le Havre", "Grenoble",
           "Dijon", "Angers", "Nîmes", "Clermont-Ferrand", "Aix-en-Provence", "Brest", "Tours",
           "Amiens", "Limoges", "Annecy", "Perpignan", "Metz", "Besançon", "Orléans", "Rouen",
           "Caen", "Nancy", "Avignon", "La Rochelle", "Poitiers", "Pau", "Bayonne", "Vannes", "Arles"],
    "BE": ["Bruxelles", "Liège", "Namur", "Charleroi", "Gand", "Anvers", "Mons"],
    "CH": ["Genève", "Lausanne", "Zurich", "Berne", "Neuchâtel", "Fribourg"],
    "ES": ["Madrid", "Barcelone", "Valence", "Séville", "Bilbao", "Malaga"],
}

# --- Catégories : poids de ventes, prix log-normal (médiane €, sigma), noms de produits ---
CATEGORIES = {
    "Mode": {"weight": 0.22, "median": 35, "sigma": 0.6,
             "nouns": ["Robe", "T-shirt", "Pull", "Jean", "Veste"]},
    "Maison": {"weight": 0.16, "median": 45, "sigma": 0.8,
               "nouns": ["Lampe", "Coussin", "Vase", "Plaid", "Bougie"]},
    "Beauté": {"weight": 0.12, "median": 22, "sigma": 0.5,
               "nouns": ["Savon", "Crème", "Sérum", "Huile", "Baume"]},
    "High-tech": {"weight": 0.12, "median": 120, "sigma": 0.9,
                  "nouns": ["Casque", "Enceinte", "Chargeur", "Clavier", "Montre connectée"]},
    "Épicerie fine": {"weight": 0.08, "median": 18, "sigma": 0.5,
                      "nouns": ["Miel", "Confiture", "Huile d'olive", "Thé", "Chocolat"]},
    "Sport": {"weight": 0.09, "median": 50, "sigma": 0.8,
              "nouns": ["Tapis de yoga", "Gourde", "Legging", "Sac de sport", "Haltères"]},
    "Jouets": {"weight": 0.07, "median": 28, "sigma": 0.6,
               "nouns": ["Puzzle", "Peluche", "Jeu de société", "Train en bois", "Poupée"]},
    "Bijoux": {"weight": 0.06, "median": 60, "sigma": 0.9,
               "nouns": ["Bague", "Collier", "Bracelet", "Boucles d'oreilles", "Pendentif"]},
    "Livres & Papeterie": {"weight": 0.04, "median": 15, "sigma": 0.5,
                           "nouns": ["Carnet", "Agenda", "Affiche", "Stylo", "Livre illustré"]},
    "Animalerie": {"weight": 0.04, "median": 25, "sigma": 0.6,
                   "nouns": ["Collier pour chien", "Panier", "Jouet pour chat", "Gamelle", "Friandises"]},
}
COLORS = ["noir", "blanc", "bleu", "vert", "rouge", "beige", "rose", "gris"]
EMAIL_DOMAINS = ["example.com", "example.fr", "example.org", "example.net"]

# --- Anomalies injectées ---
SUSPICIOUS_PRICE_RATE = 0.001      # toujours actif : 0,01 € ou 10x le prix
DEFECT_NULL_CUSTOMER_RATE = 0.002  # défauts qualité, désactivables via QUALITY_DEFECTS
DEFECT_FUTURE_DATE_RATE = 0.001
DEFECT_DUPLICATE_ORDER_RATE = 0.001

ANOMALIES = json.loads((Path(__file__).parent / "anomalies.json").read_text(encoding="utf-8"))
