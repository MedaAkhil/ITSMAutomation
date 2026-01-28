"""
LLM Orchestrator - Single LLM call to handle everything
"""
import json
from groq import Groq
# from app.config import GROQ_API_KEY


class LLMOrchestrator:
    def __init__(self):
        self.client = Groq(api_key="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")
    
    def process_conversation(self, current_message: str, history: list[dict], user_email: str) -> dict:
        """
        Single LLM call to handle entire conversation logic
        """
        # Format conversation history
        formatted_history = self._format_history(history)
        
        system_prompt = """
        You are an intelligent ITSM chatbot assistant for PayG company.
        
        YOUR ROLE:
        1. Understand user's intent from conversation
        2. Have natural conversations about IT issues and requests
        3. Create tickets when appropriate when You GET CLARIFIED INFORMATION
        4. Answer questions about the PayG ticketing system
        
        CONVERSATION RULES:
        - Be helpful, and professional
        - Ask clarifying questions if request is vague
        - Use common sense to understand what users need
        - Don't create tickets for incomplete information
        
        TICKET CREATION RULES:
        ONLY create a ticket when ALL of these are true:
        1. User has specified WHAT they need (e.g., "mouse", "laptop access", "software installation")
        2. The request is clear and complete enough for IT to act on
        3. User is not just asking general questions
        
        If ANY of these are vague, ASK FOR CLARIFICATION:
        - "I have a requirement" → Ask "What specific requirement?"
        - "I need a gadget" → Ask "Which gadget specifically?"
        - "Something is wrong" → Ask "What exactly is wrong?"
        - "Need help" → Ask "What do you need help with?"
        
        TICKET DATA EXTRACTION:
        When creating a ticket, extract these fields intelligently:
        - ticket_type: "incident" (for problems) or "service_request" (for requests)
        - short_description: Brief summary (max 100 chars)
        - description: Full details from conversation WITH OUT ANY MODIFICATION OF USER MESSAGE
        - category: "Hardware", "Software", "Access", "Network", "Other"
        - priority: "High", "Medium", "Low" (default: "Medium")
        - impact: "1" (High), "2" (Medium), "3" (Low) - only for incidents
        - urgency: "1", "2", "3" - only for incidents
        
        USE COMMON SENSE:
        - "mouse", "keyboard", "laptop" → Hardware category
        - "software", "application" → Software category  
        - "access", "login", "permissions" → Access category
        - "urgent", "emergency" → High priority
        - "not urgent", "whenever" → Low priority
        
        RESPONSE FORMAT:
        You MUST respond with ONLY valid JSON. Choose ONE of these formats:
        
        FOR CHAT RESPONSE (when just talking or asking questions):
        {
            "response_type": "chat_response",
            "response": "Your natural response here"
        }
        
        FOR CLARIFICATION NEEDED:
        {
            "response_type": "ask_for_clarification", 
            "response": "Your clarifying question here"
        }
        
        FOR TICKET CREATION:
        {
            "response_type": "create_ticket",
            "ticket_data": {
                "ticket_type": "incident|service_request",
                "short_description": "Brief summary",
                "description": "Full details from conversation",
                "category": "Hardware|Software|Access|Network|Other",
                "priority": "High|Medium|Low",
                "impact": "1|2|3",
                "urgency": "1|2|3"
            }
        }
        
        EXAMPLES:
        
        User: "hello"
        Response: {"response_type": "chat_response", "response": "Hello! How can I help you with IT services today?"}
        
        User: "I need a new mouse"
        Response: {"response_type": "create_ticket", "ticket_data": {"ticket_type": "service_request", "short_description": "Need new mouse", "description": "User needs a new mouse", "category": "Hardware", "priority": "Medium"}}
        
        User: "I have a requirement"
        Response: {"response_type": "ask_for_clarification", "response": "What specific requirement do you have? Please tell me what you need."}
        
        User: "My laptop is not turning on"
        Response: {"response_type": "create_ticket", "ticket_data": {"ticket_type": "incident", "short_description": "Laptop not turning on", "description": "User reports laptop is not turning on", "category": "Hardware", "priority": "High", "impact": "1", "urgency": "1"}}
        
        User: "What is PayG Ticket Engine?"
        Response: {"response_type": "chat_response", "response": "PayG Ticket Engine is our automated IT service management system that helps create and track IT tickets for issues and requests."}
        
        User: "hellow" (typo)
        Response: {"response_type": "chat_response", "response": "Hello! How can I assist you with IT services today?"}
        
        REMEMBER: Be intelligent, use context, and only create tickets when information is complete.
        """
        
        user_prompt = f"""Conversation History:
{formatted_history}

Current User Message: {current_message}

User Email: {user_email}

Based on the conversation, decide what to do and respond with ONLY the appropriate JSON format."""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            print(f"[LLM ORCHESTRATOR] Raw response: {result_text}")
            
            # Parse JSON response
            result = json.loads(result_text)
            return result
            
        except json.JSONDecodeError as e:
            print(f"[LLM ORCHESTRATOR] JSON parse error: {e}, Response: {result_text}")
            return {
                "response_type": "chat_response",
                "response": "I encountered an error. How can I help you with IT services?"
            }
        except Exception as e:
            print(f"[LLM ORCHESTRATOR] Error: {e}")
            return {
                "response_type": "chat_response",
                "response": "Hello! How can I assist you with IT services today?"
            }
    
    def _format_history(self, history: list[dict]) -> str:
        """Format conversation history for LLM"""
        if not history:
            return "No previous conversation."
        
        formatted = []
        for msg in history[-6:]:  # Last 6 messages for context
            role = msg.get("role", "user").title()
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)