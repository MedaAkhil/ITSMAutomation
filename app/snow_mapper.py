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
