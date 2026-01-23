import imaplib
import email
from email.header import decode_header
from app.config import *
from app.models import get_last_uid, set_last_uid
from datetime import datetime


def fetch_new_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("INBOX")

    last_uid = get_last_uid()
    search_criteria = "ALL" if not last_uid else f"(UID {int(last_uid)+1}:*)"

    status, data = mail.uid("search", None, search_criteria)
    uids = data[0].split()

    emails = []

    for uid in uids:
        _, msg_data = mail.uid("fetch", uid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject, enc = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(enc or "utf-8", errors="ignore")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        emails.append({
            "message_id": msg["Message-ID"],
            "from": msg["From"],
            "subject": subject,
            "body": body,
            "uid": int(uid),
            "status": "unprocessed",
            "intent_processed": False,
            "received_at": datetime.now()
        })

        set_last_uid(int(uid))

    mail.logout()
    return emails