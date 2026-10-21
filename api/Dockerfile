FROM python:3.11-slim

WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Le générateur est partagé avec l'API (contexte de build = racine du repo)
COPY generator/ generator/
COPY api/ api/

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "api.app:app"]
