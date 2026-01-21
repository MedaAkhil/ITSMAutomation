import json
from app.models import get_unprocessed_emails, save_intent
from app.text_cleaner import clean_email_text
from app.ai_intent import detect_intent
from app.snow_client import create_incident
from app.snow_mapper import map_intent_to_incident
from app.models import save_snow_incident


def safe_json_parse(text: str):
    if not text:
        return None

    text = text.strip()

    # Try to extract JSON block if extra text exists
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    try:
        return json.loads(text[start:end+1])
    except Exception:
        return None

def process_intents():
    emails = list(get_unprocessed_emails())
    print(f"[INTENT] New emails to process: {len(emails)}")

    for email in emails:
        clean_text = clean_email_text(
            email["subject"] + "\n" + email["body"]
        )

        print("detect intent triggered:", clean_text[:200])
        if not is_it_related(clean_text):
            print("[SKIP] Non-IT email:", email["subject"])
            save_intent(
                email["message_id"],
                {
                    "intent": "non_it",
                    "ticket_required": False,
                    "confidence": 0.99
                },
                clean_text
            )
            continue

        ai_response = detect_intent(clean_text)

        intent_json = safe_json_parse(ai_response)
        if intent_json.get("ticket_required") is True:
            incident_payload = map_intent_to_incident(email, intent_json, clean_text)

            result = create_incident(incident_payload)

            save_snow_incident(
                email["message_id"],
                result["number"],
                result["sys_id"]
            )

            print("[SNOW] Incident created:", result["number"])


        if not intent_json:
            print("[SKIP] Invalid AI output, marking as processed")
            save_intent(
                email["message_id"],
                {
                    "intent": "unknown",
                    "ticket_required": False,
                    "confidence": 0.0
                },
                clean_text
            )
            continue

        save_intent(
            email["message_id"],
            intent_json,
            clean_text
        )

        print("[INTENT SAVED]", intent_json.get("intent"))

def is_it_request(text: str) -> bool:
    keywords = [
        "laptop", "mouse", "keyboard", "vpn", "password",
        "access", "login", "wifi", "software", "install",
        "issue", "problem", "not working"
    ]
    text = text.lower()
    return any(k in text for k in keywords)
def is_it_related(text: str) -> bool:
    keywords = [
        "laptop", "mouse", "keyboard", "vpn", "password",
        "login", "access", "wifi", "network",
        "software", "install", "issue", "problem",
        "not working", "damaged", "broken"
    ]
    t = text.lower()
    return any(k in t for k in keywords)
