"""
Intent classification for chatbot messages
"""
from groq import Groq
import json

# Initialize Groq client
client = Groq(api_key="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")

SYSTEM_PROMPT = """
You are an intent classifier for an ITSM chatbot. Classify the user's message.

INTENTS:
1. incident - User wants to report an IT problem/issue
   Examples: "my laptop is broken", "can't login", "printer not working", 
             "system is down", "network issue", "software error"

2. service_request - User wants to request IT equipment or services
   Examples: "need a new mouse", "request software", "need access", 
             "want a monitor", "install application"

3. faq - User is asking about PayG Ticket Engine or general IT questions
   Examples: "what is PayG Ticket Engine", "how to raise ticket", 
             "what is SLA", "contact IT", "ticket types"

4. ticket_status - User wants to check status of existing ticket
   Examples: "status of ticket", "when will be fixed", "ticket update"

5. greeting - User is greeting or asking for help
   Examples: "hello", "hi", "help", "what can you do", "hey"

6. out_of_scope - Message is not related to ITSM
   Examples: "weather", "joke", "vacation", "personal questions"

STRICT RULES:
- Return ONLY valid JSON
- No explanations, no markdown

Schema:
{
    "intent_type": "incident | service_request | faq | ticket_status | greeting | out_of_scope",
    "confidence": "high | medium | low"
}
"""


def classify_chat_intent(message: str) -> dict:
    """
    Simple intent classification for backward compatibility
    """
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hi", "hello", "hey", "help"]):
        return {"intent_type": "greeting"}
    
    if any(word in message_lower for word in ["broken", "not working", "error", "issue"]):
        return {"intent_type": "incident"}
    
    if any(word in message_lower for word in ["need", "want", "request", "new"]):
        return {"intent_type": "service_request"}
    
    if any(word in message_lower for word in ["what is", "how to", "faq"]):
        return {"intent_type": "faq"}
    
    return {"intent_type": "unclear"}