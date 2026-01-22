from datetime import datetime
from app.db import emails_col, tickets_col

# 1️⃣ Mark email as ignored
def mark_ignored(email):
    emails_col.update_one(
        {"_id": email["_id"]},
        {"$set": {"status": "ignored"}}
    )


# 2️⃣ Check duplicate ticket
def is_duplicate(fingerprint):
    existing = tickets_col.find_one({
        "fingerprint": fingerprint,
        "status": "open"
    })
    return existing is not None


# 3️⃣ Save created ticket
def save_ticket(email, ticket_number, fingerprint, ticket_type):
    tickets_col.insert_one({
        "fingerprint": fingerprint,
        "ticket_number": ticket_number,
        "type": ticket_type,
        "status": "open",
        "created_at": datetime.utcnow()
    })

    emails_col.update_one(
        {"_id": email["_id"]},
        {
            "$set": {
                "status": "processed",
                "ticket_number": ticket_number,
                "fingerprint": fingerprint
            }
        }
    )
