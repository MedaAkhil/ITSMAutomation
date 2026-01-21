import imaplib

EMAIL = "medaakhilaeshai@gmail.com"
PASSWORD = "ajtrgdfrnuiijxew"

imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
imap.login(EMAIL, PASSWORD)
imap.select("INBOX")

status, messages = imap.search(None, "ALL")
print("Emails:", len(messages[0].split()))

imap.logout()