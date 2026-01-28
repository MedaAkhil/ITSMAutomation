"""
Intelligent ticket creation using LLM
"""
import json
import re
from groq import Groq
# from app.config import GROQ_API_KEY


class LLMTicketCreator:
    def __init__(self):
        self.client = Groq(api_key="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")
    
    def analyze_message(self, message: str, conversation_context: dict = None) -> dict:
        """
        Analyze user message to decide what action to take
        """
        system_prompt = """
        You are an intelligent ITSM assistant. Analyze the user's message and decide what to do.
        
        RULES:
        1. ONLY create ticket if user provides SPECIFIC details about what they need
        2. If message is VAGUE or GENERAL, ask for more details
        3. Use common sense to determine if enough information is provided
        
        EXAMPLES:
        ✅ CREATE TICKET (specific enough):
        - "I need a new mouse" → Service request for mouse (Hardware)
        - "My laptop screen is broken" → Incident for laptop screen (Hardware)
        - "Need access to SharePoint" → Service request for SharePoint access (Access)
        - "Adobe Photoshop installation" → Service request for software (Software)
        
        ❌ ASK FOR DETAILS (too vague):
        - "I have a requirement" → Ask "What is the requirement?"
        - "I need something" → Ask "What do you need?"
        - "Need a gadget" → Ask "Which gadget do you need?"
        - "Having an issue" → Ask "What issue are you experiencing?"
        - "Something is wrong" → Ask "Can you describe what's wrong?"
        
        Return ONLY valid JSON with this structure:
        {
            "action": "create_ticket | ask_for_details | faq | unclear",
            "ticket_type": "incident | service_request | unknown",
            "collected_data": {
                "description": "user's detailed description if specific",
                "short_description": "brief summary if specific",
                "category": "extracted category if specific (Hardware/Software/Access/Other)",
                "priority": "extracted priority if mentioned (High/Medium/Low)"
            },
            "missing_info": ["list", "of", "missing", "fields"],
            "question": "if action is ask_for_details, what specific question to ask"
        }
        
        BE STRICT: Only create ticket if SPECIFIC item/issue is mentioned.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            print(f"[LLM TICKET CREATOR] Analysis result: {result}")
            
            # Validate the result
            result = self._validate_analysis(result, message)
            
            return result
            
        except Exception as e:
            print(f"[LLM TICKET CREATOR] Error: {e}")
            return self._fallback_analysis(message)
    
    def _validate_analysis(self, analysis: dict, original_message: str) -> dict:
        """Validate and correct the LLM analysis if needed"""
        message_lower = original_message.lower().strip()
        
        # List of vague phrases that should NEVER trigger ticket creation
        vague_phrases = [
            "i have a", "i need a", "i want a", "i require a",
            "i have an", "i need an", "i want an", "i require an",
            "i have some", "i need some", "i want some",
            "new requirement", "new request", "new thing",
            "something", "thing", "item", "gadget", "device",
            "help", "issue", "problem", "trouble"
        ]
        
        # Check if message is vague but LLM said to create ticket
        if analysis.get("action") == "create_ticket":
            # Check if the message contains specific IT terms
            specific_terms = [
                "mouse", "keyboard", "laptop", "monitor", "printer",
                "software", "access", "login", "password", "vpn",
                "email", "network", "wifi", "internet", "server",
                "broken", "not working", "crash", "error", "install"
            ]
            
            has_specific_term = any(term in message_lower for term in specific_terms)
            is_vague = any(phrase in message_lower for phrase in vague_phrases)
            
            # If message is vague and doesn't have specific terms, ask for details
            if is_vague and not has_specific_term:
                print(f"[VALIDATION] Overriding: Vague message '{original_message}' should not create ticket")
                
                # Generate appropriate question based on the vague phrase
                question = self._generate_clarification_question(original_message)
                
                return {
                    "action": "ask_for_details",
                    "ticket_type": "unknown",
                    "collected_data": {},
                    "missing_info": ["description", "category"],
                    "question": question
                }
        
        return analysis
    
    def _generate_clarification_question(self, message: str) -> str:
        """Generate a specific clarification question based on the vague message"""
        message_lower = message.lower()
        
        if "requirement" in message_lower:
            return "What specific requirement do you have?"
        elif "gadget" in message_lower or "device" in message_lower:
            return "Which specific gadget or device do you need?"
        elif "something" in message_lower or "thing" in message_lower:
            return "What specific item or issue are you referring to?"
        elif "need" in message_lower or "want" in message_lower:
            if "new" in message_lower:
                return "What new item do you need?"
            else:
                return "What do you need?"
        elif "issue" in message_lower or "problem" in message_lower:
            return "What specific issue are you experiencing?"
        elif "help" in message_lower:
            return "What do you need help with?"
        else:
            return "Can you please provide more specific details about what you need?"
    
    def _fallback_analysis(self, message: str) -> dict:
        """Fallback analysis when LLM fails"""
        message_lower = message.lower()
        
        # Check if message is specific enough
        specific_keywords = [
            "mouse", "keyboard", "laptop", "monitor", "printer",
            "software", "access", "login", "vpn", "email",
            "broken", "not working", "install", "password"
        ]
        
        vague_keywords = [
            "requirement", "gadget", "device", "something", 
            "thing", "item", "help", "issue", "problem"
        ]
        
        has_specific = any(keyword in message_lower for keyword in specific_keywords)
        has_vague = any(keyword in message_lower for keyword in vague_keywords)
        
        # If vague and not specific, ask for details
        if has_vague and not has_specific:
            question = self._generate_clarification_question(message)
            return {
                "action": "ask_for_details",
                "question": question,
                "collected_data": {},
                "missing_info": ["description", "category"]
            }
        
        # Check for incidents
        incident_keywords = ["broken", "not working", "error", "crash", "down"]
        is_incident = any(keyword in message_lower for keyword in incident_keywords)
        
        # Check for service requests
        request_keywords = ["need", "want", "request", "new", "install"]
        is_request = any(keyword in message_lower for keyword in request_keywords)
        
        # Extract category
        category = "Other"
        if "mouse" in message_lower or "keyboard" in message_lower or "laptop" in message_lower:
            category = "Hardware"
        elif "software" in message_lower or "app" in message_lower:
            category = "Software"
        elif "access" in message_lower or "login" in message_lower:
            category = "Access"
        
        if is_incident and has_specific:
            return {
                "action": "create_ticket",
                "ticket_type": "incident",
                "collected_data": {
                    "description": message,
                    "short_description": message[:80],
                    "category": category,
                    "priority": "Medium"
                },
                "missing_info": []
            }
        elif is_request and has_specific:
            return {
                "action": "create_ticket",
                "ticket_type": "service_request",
                "collected_data": {
                    "description": message,
                    "short_description": message[:80],
                    "category": category
                },
                "missing_info": []
            }
        else:
            return {
                "action": "ask_for_details",
                "question": "Can you please provide more specific details?",
                "collected_data": {},
                "missing_info": ["description"]
            }
    
    def extract_ticket_data(self, conversation_history: list) -> dict:
        """
        Extract ticket data from conversation history using LLM
        """
        # Format conversation
        conversation_text = "\n".join([
            f"{msg.get('role', 'user').title()}: {msg.get('content', '')}"
            for msg in conversation_history[-10:]
        ])
        
        system_prompt = """
        Extract ticket information from conversation. Return ONLY JSON:
        {
            "ticket_type": "incident | service_request",
            "short_description": "specific summary",
            "description": "full details",
            "category": "Hardware | Software | Access | Network | Other",
            "priority": "High | Medium | Low",
            "impact": "1 | 2 | 3",
            "urgency": "1 | 2 | 3"
        }
        
        Important: Only extract if specific details are provided.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": conversation_text}
                ],
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"[LLM EXTRACT] Error: {e}")
            return None