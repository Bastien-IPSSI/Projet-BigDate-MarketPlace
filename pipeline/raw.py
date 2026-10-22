"""Raw layer dans MinIO (s3://data-lake/raw/orders/dt=YYYY-MM-DD/data.json)."""
import json
import os

import boto3


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )


def raw_key(day):
    return f"raw/orders/dt={day}/data.json"


def write_raw(day, orders):
    """Écrit le JSON brut de l'API. Réécrire le même chemin écrase l'ancien fichier : idempotent."""
    s3_client().put_object(
        Bucket=os.environ["MINIO_BUCKET"],
        Key=raw_key(day),
        Body=json.dumps(orders, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{os.environ['MINIO_BUCKET']}/{raw_key(day)}"


def read_raw(day):
    """Relit le JSON brut d'une journée, sans appeler l'API."""
    obj = s3_client().get_object(Bucket=os.environ["MINIO_BUCKET"], Key=raw_key(day))
    return json.loads(obj["Body"].read())
