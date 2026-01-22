import re
from datetime import datetime
from app.db import emails_col, tickets_col

# 1️⃣ Mark email as ignored
def mark_ignored(email):
    result = emails_col.update_one(
        {"_id": email["_id"]},
        {"$set": {
            "status": "ignored",
            "intent_processed": True,
            "processed_at": datetime.utcnow()
        }}
    )
    print(f"[MARKED IGNORED] Updated {result.modified_count} document(s) for email ID: {email.get('_id')}")


# 2️⃣ Check duplicate ticket
def is_duplicate(fingerprint):
    """Check if a similar email was already processed recently"""
    try:
        # Look for emails with same fingerprint that were processed within last 7 days
        existing = emails_col.find_one({
            "fingerprint": fingerprint,
            "intent_processed": True,
            "status": {"$ne": "ignored"},  # Don't count ignored emails
            "processed_at": {"$gte": datetime.utcnow() - timedelta(days=7)}  # Last 7 days
        })
        
        if existing:
            existing_ticket = existing.get("ticket_number", "unknown")
            print(f"[DUPLICATE FOUND] Similar to email processed on {existing.get('processed_at')}")
            print(f"[DUPLICATE FOUND] Existing ticket: {existing_ticket}")
            return True
        
        return False
    except Exception as e:
        print(f"[DUPLICATE CHECK ERROR] {e}")
        return False


# 3️⃣ Save created ticket
def save_ticket(email, ticket_number, fingerprint, ticket_type):
    tickets_col.insert_one({
        "fingerprint": fingerprint,
        "ticket_number": ticket_number,
        "type": ticket_type,
        "status": "open",
        "created_at": datetime.utcnow(),
        "email_id": email.get("_id"),
        "subject": email.get("subject")
    })

    emails_col.update_one(
        {"_id": email["_id"]},
        {
            "$set": {
                "status": "processed",
                "ticket_number": ticket_number,
                "fingerprint": fingerprint,
                "processed_at": datetime.utcnow()
            }
        }
    )


def extract_email(from_field: str) -> str:
    """
    Input:  'Meda Akhil <meda8125@gmail.com>'
    Output: 'meda8125@gmail.com'
    """
    if not from_field:
        return ""
    
    match = re.search(r'<(.+?)>', from_field)
    if match:
        return match.group(1)
    return from_field.strip()