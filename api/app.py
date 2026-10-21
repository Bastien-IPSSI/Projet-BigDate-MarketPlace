"""API Flask qui sert les données du générateur.

Premier commit : squelette avec /health uniquement. Les routes /orders, /sellers,
/products et /customers seront développées ultérieurement.
"""
from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
