import hashlib

def generate_fingerprint(sender, subject, intent_type):
    raw = f"{sender}|{subject.lower()}|{intent_type}"
    return hashlib.sha256(raw.encode()).hexdigest()
