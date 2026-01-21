from pymongo import MongoClient
from app.config import *

client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION]
meta_collection = client[DB_NAME]["metadata"]
meta = client[DB_NAME]["metadata"]

def email_exists(message_id):
    return collection.find_one({"message_id": message_id}) is not None

def save_email(email):
    collection.insert_one(email)

def get_unprocessed_emails():
    return collection.find({"intent_processed": {"$ne": True}})

def save_intent(message_id, intent_data, clean_text):
    collection.update_one(
        {"message_id": message_id},
        {
            "$set": {
                "intent_processed": True,
                "intent": intent_data,
                "clean_text": clean_text
            }
        }
    )

def get_bootstrap_done():
    return meta.find_one({"_id": "bootstrap"}) is not None

def mark_bootstrap_done():
    meta.insert_one({"_id": "bootstrap"})
def get_last_uid():
    doc = meta_collection.find_one({"_id": "imap_state"})
    return doc["last_uid"] if doc else None

def set_last_uid(uid):
    meta_collection.update_one(
        {"_id": "imap_state"},
        {"$set": {"last_uid": uid}},
        upsert=True
    )

def save_snow_incident(message_id, incident_number, sys_id):
    collection.update_one(
        {"message_id": message_id},
        {
            "$set": {
                "snow": {
                    "incident_number": incident_number,
                    "sys_id": sys_id,
                    "status": "created"
                }
            }
        }
    )
