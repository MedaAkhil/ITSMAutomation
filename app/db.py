from pymongo import MongoClient
from app.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["itsm_automation"]

emails_col = db["emails"]
tickets_col = db["tickets"]
