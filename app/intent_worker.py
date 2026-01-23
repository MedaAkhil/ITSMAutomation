from datetime import datetime
import json
from app.models import get_unprocessed_emails, save_intent
from app.text_cleaner import clean_email_text
from app.ai_intent import detect_intent
# from app.snow_client import create_incident
from app.snow_mapper import map_intent_to_incident
from app.models import save_snow_incident

from app.text_cleaner import is_newsletter
from app.snow_client import snow_post, get_user_sys_id
from app.snow_mapper import map_incident, map_service_request
from app.dedup import generate_fingerprint
from app.email_reply import send_reply
from app.helpers import extract_email, mark_ignored, is_duplicate, save_ticket

from app.db import update_email
from app.db import emails_col


def safe_json_parse(text: str):
    if not text:
        return None

    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    try:
        return json.loads(text[start:end+1])
    except Exception:
        return None

def process_intents():
    try:
        emails_cursor = get_unprocessed_emails()
        emails = list(emails_cursor)
        print(f"[INTENT LOOP] Emails to process: {len(emails)}")
        
        if not emails:
            print("[INTENT LOOP] No unprocessed emails found")
            return

        for email in emails:
            print(f"[PROCESSING EMAIL] ID: {email.get('_id')}, Subject: {email.get('subject', 'No Subject')}")
            print(f"[EMAIL DETAILS] From: {email.get('from')}, Status: {email.get('status')}")

            raw_text = email.get("subject", "") + "\n" + email.get("body", "")
            
            if not raw_text.strip():
                print("[WARNING] Empty email content, marking as ignored")
                mark_ignored(email)
                continue

            if is_newsletter(raw_text):
                mark_ignored(email)
                print("[IGNORED] Newsletter/Promotional email detected")
                continue

            clean_text = raw_text.strip()
            
            try:
                intent_json = detect_intent(clean_text)
                print(f"[LLM RESPONSE] Intent: {intent_json}")
            except Exception as e:
                print(f"[LLM ERROR] Failed to detect intent: {e}")
                mark_ignored(email)
                continue

            if not intent_json:
                print("[WARNING] No intent returned from LLM")
                mark_ignored(email)
                continue
                
            intent_type = intent_json.get("intent_type")
            if not intent_type or intent_type == "ignore":
                mark_ignored(email)
                print("[IGNORED] Not an incident or service request")
                continue

            sender_email = extract_email(email.get("from", ""))
            print(f"[SENDER EMAIL] Extracted: {sender_email}")
            
            fingerprint = generate_fingerprint(
                sender_email,
                email.get("subject", ""),
                intent_type
            )
            print(f"[FINGERPRINT] Generated: {fingerprint[:20]}...")

            if is_duplicate(fingerprint):
                print("[DUPLICATE] Skipping - similar open ticket exists")
                update_email(
                    email.get("message_id"),
                    {
                        "clean_text": clean_text,
                        "intent": intent_json,
                        "intent_processed": True,
                        "processed_at": datetime.utcnow(),
                        "status": "duplicate"
                    }
                )
                continue

            caller_id = get_user_sys_id(sender_email)
            if not caller_id:
                print(f"[ERROR] No ServiceNow user found for {sender_email}")
                update_email(
                    email.get("message_id"),
                    {
                        "clean_text": clean_text,
                        "intent": intent_json,
                        "intent_processed": True,
                        "processed_at": datetime.utcnow(),
                        "status": "error_no_caller"
                    }
                )
                continue

            ticket_number = None
            sys_id = None
            snow_result = None

            try:
                if intent_type == "incident":
                    print(f"[CREATING INCIDENT] Category: {intent_json.get('category')}, Priority: {intent_json.get('priority')}")
                    payload = map_incident(email, intent_json, caller_id, clean_text)
                    print(f"[INCIDENT PAYLOAD] {payload}")
                    result = snow_post("incident", payload)
                    ticket_number = result.get("number")
                    sys_id = result.get("sys_id")
                    snow_result = result
                    print(f"[INCIDENT CREATED] Ticket: {ticket_number}, Sys ID: {sys_id}")

                elif intent_type == "service_request":
                    print(f"[CREATING SERVICE REQUEST] Category: {intent_json.get('category')}")
                    payload = map_service_request(intent_json, caller_id)
                    print(f"[SERVICE REQUEST PAYLOAD] {payload}")
                    result = snow_post("sc_request", payload)
                    ticket_number = result.get("number")
                    sys_id = result.get("sys_id")
                    snow_result = result
                    print(f"[SERVICE REQUEST CREATED] Ticket: {ticket_number}, Sys ID: {sys_id}")
                    
                else:
                    print(f"[ERROR] Unknown intent type: {intent_type}")
                    mark_ignored(email)
                    continue

            except Exception as e:
                print(f"[SERVICENOW ERROR] Failed to create ticket: {e}")
                update_email(
                    email.get("message_id"),
                    {
                        "clean_text": clean_text,
                        "intent": intent_json,
                        "intent_processed": True,
                        "processed_at": datetime.utcnow(),
                        "status": "error_snow",
                        "error": str(e)
                    }
                )
                continue

            if ticket_number:
                update_result = update_email(
                    email.get("message_id"),
                    {
                        "clean_text": clean_text,
                        "intent": intent_json,
                        "intent_processed": True,
                        "processed_at": datetime.utcnow(),
                        "status": "processed",
                        "ticket_created": True,
                        "ticket_number": ticket_number,
                        "fingerprint": fingerprint,
                        "snow": {
                            "number": ticket_number,
                            "sys_id": sys_id,
                            "type": intent_type,
                            "status": "created",
                            "result": snow_result
                        }
                    }
                )
                print(f"[DB UPDATE] Updated {update_result} document(s)")

                try:
                    send_reply(sender_email, ticket_number)
                except Exception as e:
                    print(f"[REPLY ERROR] Failed to send reply: {e}")

                print(f"[COMPLETED] Successfully processed email -> Ticket {ticket_number}")
            else:
                print("[ERROR] Ticket created but no ticket number returned")

    except Exception as e:
        print(f"[INTENT LOOP ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


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