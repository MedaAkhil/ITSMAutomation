"""
FastAPI endpoints for ITSM Chatbot
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
import os

from app.chatbot.chatbot import get_chatbot

# Create FastAPI app
chatbot_app = FastAPI(
    title="ITSM Chatbot API",
    description="Chat interface for IT Service Management",
    version="2.0.0"
)

# Add CORS middleware
chatbot_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_email: str

class ChatResponse(BaseModel):
    response: str
    ticket_created: bool = False
    ticket_number: Optional[str] = None
    requires_action: bool = False
    collecting_data: bool = False
    current_step: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    chatbot: str
    active_conversations: int
    uptime: float

# Track startup time
START_TIME = time.time()

@chatbot_app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chatbot endpoint
    """
    try:
        # Validate input
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.user_email.strip() or "@" not in request.user_email:
            raise HTTPException(status_code=400, detail="Valid email is required")
        
        # Get chatbot instance
        chatbot = get_chatbot()
        
        # Process message
        result = chatbot.process_message(
            user_email=request.user_email,
            message=request.message
        )
        
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT API ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_app.post("/reset/{user_email}")
async def reset_conversation(user_email: str):
    """
    Reset conversation for a user
    """
    try:
        chatbot = get_chatbot()
        success = chatbot.cancel_conversation(user_email)
        
        return {
            "status": "success" if success else "no_active_conversation",
            "message": f"Conversation reset for {user_email}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_app.get("/health")
async def health_check() -> HealthResponse:
    """
    Health check endpoint
    """
    try:
        chatbot = get_chatbot()
        stats = chatbot.conversations.get_conversation_stats()
        
        return HealthResponse(
            status="healthy",
            chatbot="operational",
            active_conversations=stats["total_active"],
            uptime=time.time() - START_TIME
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            chatbot=f"error: {str(e)}",
            active_conversations=0,
            uptime=time.time() - START_TIME
        )

@chatbot_app.get("/stats")
async def get_stats():
    """
    Get chatbot statistics
    """
    try:
        chatbot = get_chatbot()
        stats = chatbot.conversations.get_conversation_stats()
        
        return {
            "active_conversations": stats["total_active"],
            "collecting_data": stats["collecting_data"],
            "by_type": stats["by_type"],
            "faq_entries": len(chatbot.faq.faq_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_app.get("/faq")
async def get_faq():
    """
    Get FAQ questions
    """
    try:
        chatbot = get_chatbot()
        faq_list = []
        
        for faq in chatbot.faq.faq_data:
            faq_list.append({
                "questions": faq["questions"],
                "answer_preview": faq["answer"][:100] + "..."
            })
        
        return {"faq_count": len(faq_list), "faqs": faq_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the HTML interface
@chatbot_app.get("/")
async def serve_chat_interface():
    """Serve the chatbot HTML interface"""
    return FileResponse("app/chatbot/static/index.html")

# Mount static files
os.makedirs("app/chatbot/static", exist_ok=True)
chatbot_app.mount("/static", StaticFiles(directory="app/chatbot/static"), name="static")