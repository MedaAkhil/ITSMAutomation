def map_intent_to_incident(email, intent, clean_text):
    priority_map = {
        "high": (1, 1),
        "medium": (2, 2),
        "low": (3, 3)
    }

    urgency, impact = priority_map.get(
        intent.get("priority", "medium"),
        (2, 2)
    )

    return {
        "short_description": intent.get("short_description") or email["subject"],
        "description": clean_text,
        "category": intent.get("category", "hardware"),
        "subcategory": intent.get("subcategory", ""),
        "urgency": urgency,
        "impact": impact
    }
def map_incident(email, intent, caller_id, clean_text):
    return {
        "short_description": intent["short_description"],
        "description": clean_text,
        "caller_id": caller_id,
        "category": intent["category"],
        "impact": 3,
        "urgency": 3
    }

def map_service_request(intent, caller_id):
    return {
        "short_description": f"Request: {intent['short_description']}",
        "requested_for": caller_id,
        "approval": "requested",
        "request_state": "pending_approval"
    }
