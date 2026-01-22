import json
from app.models import get_unprocessed_emails, save_intent
from app.text_cleaner import clean_email_text
from app.ai_intent import detect_intent
from app.snow_client import create_incident
from app.snow_mapper import map_intent_to_incident
from app.models import save_snow_incident

from app.text_cleaner import is_newsletter
from app.snow_client import snow_post, get_user_sys_id
from app.snow_mapper import map_incident, map_service_request
from app.dedup import generate_fingerprint
from app.email_reply import send_reply
from app.helpers import mark_ignored, is_duplicate, save_ticket



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
    emails = get_unprocessed_emails()

    for email in emails:
        text = email["subject"] + "\n" + email["body"]

        if is_newsletter(text):
            mark_ignored(email)
            continue

        intent = detect_intent(text)

        if intent["intent_type"] == "ignore":
            mark_ignored(email)
            continue

        fingerprint = generate_fingerprint(
            email.get("from_email", "unknown@system"),
            email["subject"],
            intent["intent_type"]
        )

        if is_duplicate(fingerprint):
            continue

        caller_id = get_user_sys_id(
            email.get("from_email", "")
        )

        if intent["intent_type"] == "incident":
            payload = map_incident(email, intent, caller_id, text)
            result = snow_post("incident", payload)
            ticket = result["number"]

        elif intent["intent_type"] == "service_request":
            payload = map_service_request(intent, caller_id)
            result = snow_post("sc_request", payload)
            ticket = result["number"]

        save_ticket(
            email=email,
            ticket_number=ticket,
            fingerprint=fingerprint,
            ticket_type=intent["intent_type"]
        )
        send_reply(email.get("from_email", "unknown@system"), ticket)

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
