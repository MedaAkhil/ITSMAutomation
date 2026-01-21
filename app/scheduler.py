from app.models import email_exists, save_email, get_bootstrap_done, mark_bootstrap_done
from app.imap_client import fetch_new_emails
import time

def poll_emails():
    first_run = not get_bootstrap_done()

    while True:
        emails = fetch_new_emails()

        for e in emails:
            # 🔥 ignore old emails on first startup
            if first_run:
                continue

            if not email_exists(e["message_id"]):
                save_email(e)
                print("[NEW EMAIL]", e["subject"])

        if first_run:
            mark_bootstrap_done()
            print("[BOOTSTRAP] Ignored old unread emails")

        first_run = False
        time.sleep(60)
