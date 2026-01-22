import requests
from app.config import SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD

BASE_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table"

def create_incident(payload: dict):
    return snow_post("incident", payload)
    # url = f"{SNOW_INSTANCE}/api/now/table/incident"

    # headers = {
    #     "Accept": "application/json",
    #     "Content-Type": "application/json"
    # }

    # response = requests.post(
    #     url,
    #     auth=(SNOW_USERNAME, SNOW_PASSWORD),
    #     headers=headers,
    #     json=payload,
    #     timeout=10
    # )

    # if response.status_code not in (200, 201):
    #     raise Exception(f"SNOW Error {response.status_code}: {response.text}")

    # return response.json()["result"]
def snow_post(table, payload):
    res = requests.post(
        f"{BASE_URL}/{table}",
        auth=(SNOW_USERNAME, SNOW_PASSWORD),
        headers={"Content-Type": "application/json"},
        json=payload
    )
    res.raise_for_status()
    return res.json()["result"]

def get_user_sys_id(email):
    res = requests.get(
        f"{BASE_URL}/sys_user",
        auth=(SNOW_USERNAME, SNOW_PASSWORD),
        params={"sysparm_query": f"email={email}"}
    )
    users = res.json()["result"]
    return users[0]["sys_id"] if users else None
