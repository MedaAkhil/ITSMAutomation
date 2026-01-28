"""
ITSM Chatbot - Let LLM handle everything intelligently
"""
from datetime import datetime
from typing import Dict, Any, List
import json

from app.chatbot.llm_orchestrator import LLMOrchestrator
from app.chatbot.conversation_manager import ConversationManager
from app.snow_client import snow_post, get_user_sys_id
from app.email_reply import send_reply


class ITSMChatbot:
    def __init__(self):
        self.conversations = ConversationManager()
        self.llm = LLMOrchestrator()
        print("[CHATBOT] Initialized with LLM-only intelligence")
    
    def process_message(self, user_email: str, message: str) -> Dict[str, Any]:
        """
        Process message entirely through LLM
        """
        print(f"[CHATBOT] Processing from {user_email}: {message}")
        
        # Get conversation history
        conversation = self.conversations.get_conversation(user_email)
        history = conversation.get("history", [])
        
        # Add new message to history
        history.append({"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()})
        
        # Let LLM decide everything
        llm_response = self.llm.process_conversation(message, history, user_email)
        print(f"[CHATBOT] LLM Response: {llm_response}")
        
        # Handle based on LLM decision
        response_type = llm_response.get("response_type")
        
        if response_type == "chat_response":
            # Just a regular chat response
            history.append({"role": "assistant", "content": llm_response.get("response"), "timestamp": datetime.utcnow().isoformat()})
            conversation["history"] = history
            self.conversations.update_conversation(user_email, conversation)
            
            return {
                "response": llm_response.get("response"),
                "ticket_created": False,
                "ticket_number": None,
                "requires_action": False
            }
        
        elif response_type == "create_ticket":
            # LLM has decided to create a ticket with provided data
            ticket_data = llm_response.get("ticket_data", {})
            
            # Create the ticket
            result = self._create_ticket(user_email, ticket_data)
            
            if result["success"]:
                history.append({
                    "role": "assistant", 
                    "content": result["message"],
                    "ticket_created": True,
                    "ticket_number": result["ticket_number"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                history.append({
                    "role": "assistant", 
                    "content": result["message"],
                    "ticket_created": False,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            conversation["history"] = history
            self.conversations.update_conversation(user_email, conversation)
            
            return {
                "response": result["message"],
                "ticket_created": result["success"],
                "ticket_number": result.get("ticket_number"),
                "requires_action": False
            }
        
        elif response_type == "ask_for_clarification":
            # LLM wants more information
            history.append({"role": "assistant", "content": llm_response.get("response"), "timestamp": datetime.utcnow().isoformat()})
            conversation["history"] = history
            self.conversations.update_conversation(user_email, conversation)
            
            return {
                "response": llm_response.get("response"),
                "ticket_created": False,
                "ticket_number": None,
                "requires_action": True
            }
        
        else:
            # Default fallback
            response = "I'm here to help with IT service management. How can I assist you?"
            history.append({"role": "assistant", "content": response, "timestamp": datetime.utcnow().isoformat()})
            conversation["history"] = history
            self.conversations.update_conversation(user_email, conversation)
            
            return {
                "response": response,
                "ticket_created": False,
                "ticket_number": None,
                "requires_action": False
            }
    def cancel_conversation(self, user_email: str) -> bool:
        """Cancel an ongoing conversation"""
        return self.conversations.end_conversation(user_email)
    def _create_ticket(self, user_email: str, ticket_data: Dict) -> Dict:
        """Create ticket in ServiceNow"""
        try:
            ticket_type = ticket_data.get("ticket_type", "service_request")
            caller_id = get_user_sys_id(user_email) or get_user_sys_id("admin")
            
            if ticket_type == "incident":
                payload = {
                    "short_description": ticket_data.get("short_description", "Incident from chat")[:100],
                    "description": self._format_description(user_email, ticket_data),
                    "caller_id": caller_id,
                    "category": ticket_data.get("category", "Other"),
                    "impact": self._priority_to_number(ticket_data.get("impact", "2")),
                    "urgency": self._priority_to_number(ticket_data.get("urgency", "2"))
                }
                
                result = snow_post("incident", payload)
                ticket_number = result.get("number")
                
            else:  # service_request
                payload = {
                    "short_description": ticket_data.get("short_description", "Request from chat")[:100],
                    "description": self._format_description(user_email, ticket_data),
                    "requested_for": caller_id,
                    "category": ticket_data.get("category", "Other"),
                    "approval": "requested",
                    "request_state": "pending_approval"
                }
                
                result = snow_post("sc_request", payload)
                ticket_number = result.get("number")
            
            # Send email
            if ticket_number:
                try:
                    send_reply(user_email, ticket_number)
                except Exception as e:
                    print(f"[CHATBOT] Email error: {e}")
            
            return {
                "success": True,
                "ticket_number": ticket_number,
                "message": f"✅ **Ticket Created Successfully!**\n\n"
                         f"**Ticket Number**: {ticket_number}\n"
                         f"**Summary**: {ticket_data.get('short_description', '')[:80]}...\n\n"
                         f"An email confirmation has been sent to {user_email}"
            }
            
        except Exception as e:
            print(f"[CHATBOT] Ticket creation error: {e}")
            return {
                "success": False,
                "message": f"❌ Failed to create ticket: {str(e)}"
            }
    
    def _format_description(self, user_email: str, ticket_data: Dict) -> str:
        """Format ticket description"""
        desc = f"Created via Chatbot by: {user_email}\n\n"
        desc += f"Details: {ticket_data.get('description', 'No details provided')}\n"
        
        if ticket_data.get("category"):
            desc += f"Category: {ticket_data.get('category')}\n"
        
        if ticket_data.get("priority"):
            desc += f"Priority: {ticket_data.get('priority')}\n"
        
        return desc
    
    def _priority_to_number(self, priority: str) -> str:
        """Convert priority text to number"""
        if isinstance(priority, str):
            if "high" in priority.lower():
                return "1"
            elif "low" in priority.lower():
                return "3"
        return "2"


# Singleton instance
chatbot_instance = None

def get_chatbot():
    """Get or create chatbot instance"""
    global chatbot_instance
    if chatbot_instance is None:
        chatbot_instance = ITSMChatbot()
    return chatbot_instance