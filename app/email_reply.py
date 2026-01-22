import smtplib
from email.message import EmailMessage
from app.config import SMTP_USER, SMTP_PASS

def send_reply(to_email, ticket_number):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Ticket Created – {ticket_number}"
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg.set_content(
            f"Hi,\n\nYour ticket has been created.\n\nTicket Number: {ticket_number}\n\nIT Support"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"[REPLY SENT] to {to_email}")
    except Exception as e:
        print(f"[REPLY ERROR] {e}")