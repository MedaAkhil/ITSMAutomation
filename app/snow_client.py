import requests
from app.config import SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD

BASE_URL = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table"

def get_user_sys_id(email):
    """Get user sys_id from ServiceNow, fallback to admin if not found"""
    try:
        res = requests.get(
            f"{BASE_URL}/sys_user",
            auth=(SNOW_USERNAME, SNOW_PASSWORD),
            params={"sysparm_query": f"email={email}"}
        )
        res.raise_for_status()
        users = res.json()["result"]
        
        if users:
            return users[0]["sys_id"]
        else:
            # Fallback to admin user or default user
            print(f"[WARNING] User {email} not found in ServiceNow, using fallback")
            return get_fallback_user_id()
    except Exception as e:
        print(f"[ERROR] Failed to get user: {e}")
        return get_fallback_user_id()

def get_fallback_user_id():
    """Get a default user ID (admin or a default support user)"""
    try:
        # Try to get the admin user
        res = requests.get(
            f"{BASE_URL}/sys_user",
            auth=(SNOW_USERNAME, SNOW_PASSWORD),
            params={"sysparm_query": "user_name=admin"}
        )
        res.raise_for_status()
        users = res.json()["result"]
        
        if users:
            return users[0]["sys_id"]
        else:
            # If admin not found, get any active user
            res = requests.get(
                f"{BASE_URL}/sys_user",
                auth=(SNOW_USERNAME, SNOW_PASSWORD),
                params={"sysparm_query": "active=true", "sysparm_limit": 1}
            )
            res.raise_for_status()
            users = res.json()["result"]
            
            if users:
                return users[0]["sys_id"]
            else:
                return None
    except Exception as e:
        print(f"[ERROR] Failed to get fallback user: {e}")
        return None

def snow_post(table, payload):
    """Post to ServiceNow API"""
    try:
        res = requests.post(
            f"{BASE_URL}/{table}",
            auth=(SNOW_USERNAME, SNOW_PASSWORD),
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        res.raise_for_status()
        return res.json()["result"]
    except requests.exceptions.RequestException as e:
        print(f"[SERVICENOW POST ERROR] {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[RESPONSE] Status: {e.response.status_code}")
            print(f"[RESPONSE] Body: {e.response.text}")
        raise
    except Exception as e:
        print(f"[SERVICENOW ERROR] {e}")
        raise