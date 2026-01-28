"""
Main entry point for ITSM Chatbot
"""
import uvicorn
from app.chatbot_api import chatbot_app

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 PayG ITSM Chatbot")
    print("=" * 60)
    print("\nStarting chatbot services...")
    print("\nServices will run on:")
    print("1. Chatbot Interface: http://localhost:8001")
    print("2. API Endpoint: http://localhost:8001/chat")
    print("3. API Documentation: http://localhost:8001/docs")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(
        "app.chatbot_main:chatbot_app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )