import re

NEWSLETTER_KEYWORDS = [
    "unsubscribe",
    "newsletter",
    "promotion",
    "marketing",
    "view in browser",
    "privacy policy"
]

def clean_email_text(text: str) -> str:
    text = re.sub(r"On.*wrote:", "", text, flags=re.DOTALL)
    text = re.sub(r"Thanks.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Regards.*", "", text, flags=re.IGNORECASE)
    return text.strip()


def is_newsletter(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in NEWSLETTER_KEYWORDS)