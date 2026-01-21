import re
def clean_email_text(text: str) -> str:
    text = re.sub(r"On.*wrote:", "", text, flags=re.DOTALL)
    text = re.sub(r"Thanks.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Regards.*", "", text, flags=re.IGNORECASE)
    return text.strip()