import requests
from app.config import SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD

def create_incident(payload: dict):
    url = f"{SNOW_INSTANCE}/api/now/table/incident"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        auth=(SNOW_USERNAME, SNOW_PASSWORD),
        headers=headers,
        json=payload,
        timeout=10
    )

    if response.status_code not in (200, 201):
        raise Exception(f"SNOW Error {response.status_code}: {response.text}")

    return response.json()["result"]
