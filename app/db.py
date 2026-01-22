from pymongo import MongoClient
from app.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["itsm"]

emails_col = db["emails"]
tickets_col = db["tickets"]

def update_email(message_id: str, update_data: dict):
    try:
        result = emails_col.update_one(
            {"message_id": message_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            print(f"[WARNING] No email found with message_id: {message_id}")
        return result.modified_count
    except Exception as e:
        print(f"[DB UPDATE ERROR] {e}")
        return 0