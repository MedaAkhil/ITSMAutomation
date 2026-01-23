from app.models import email_exists, save_email, get_bootstrap_done, mark_bootstrap_done, set_last_uid
from app.imap_client import fetch_new_emails
import time

def poll_emails():
    if not get_bootstrap_done():
        print("[BOOTSTRAP] Initializing IMAP state...")

        emails = fetch_new_emails()
        if emails:
            last_uid = max(e["uid"] for e in emails)
            set_last_uid(last_uid)

        mark_bootstrap_done()
        print("[BOOTSTRAP] Ignored all existing emails")
    
    while True:
        try:
            emails = fetch_new_emails()

            for e in emails:
                if not email_exists(e["message_id"]):
                    save_email(e)
                    print(f"[NEW EMAIL SAVED TO DB] Subject: {e['subject']}")
        
        except Exception as e:
            print(f"[POLL ERROR] {e}")
        
        time.sleep(10)