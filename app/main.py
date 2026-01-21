from fastapi import FastAPI
import threading
from app.scheduler import poll_emails
from app.intent_worker import process_intents
import time

app = FastAPI(title="ITSM Email Ingestor")

@app.on_event("startup")
def start_background_jobs():
    threading.Thread(target=poll_emails, daemon=True).start()

    def intent_loop():
        while True:
            process_intents()
            time.sleep(30)

    threading.Thread(target=intent_loop, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )