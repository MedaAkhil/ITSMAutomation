"""
Manages conversation state
"""
from datetime import datetime, timedelta
from typing import Dict, Any

class ConversationManager:
    def __init__(self, timeout_minutes: int = 60):
        self.conversations = {}
        self.timeout = timedelta(minutes=timeout_minutes)
    
    def get_conversation(self, user_id: str) -> Dict[str, Any]:
        """Get or create conversation"""
        self._cleanup_expired()
        
        if user_id in self.conversations:
            conv = self.conversations[user_id]
            conv["last_activity"] = datetime.utcnow()
        else:
            conv = {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "history": []
            }
            self.conversations[user_id] = conv
        
        return conv
    
    def update_conversation(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update conversation"""
        if user_id in self.conversations:
            self.conversations[user_id].update(updates)
            self.conversations[user_id]["last_activity"] = datetime.utcnow()
            return True
        return False
    
    def end_conversation(self, user_id: str) -> bool:
        """End conversation"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            return True
        return False
    
    def _cleanup_expired(self):
        """Clean up expired conversations"""
        expired = []
        now = datetime.utcnow()
        
        for user_id, conv in self.conversations.items():
            if now - conv["last_activity"] > self.timeout:
                expired.append(user_id)
        
        for user_id in expired:
            del self.conversations[user_id]