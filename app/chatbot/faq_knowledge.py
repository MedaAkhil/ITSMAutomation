"""
FAQ knowledge base for PayG Ticket Engine
"""
import re

class FAQKnowledgeBase:
    def __init__(self):
        self.faq_data = self._load_faq_data()
    
    def _load_faq_data(self):
        """Load FAQ questions and answers"""
        return [
            {
                "questions": [
                    "what is payg ticket engine",
                    "what is payg ticket system",
                    "tell me about payg ticket",
                    "explain payg ticket engine",
                    "what does payg ticket engine do"
                ],
                "answer": "🚀 **PayG Ticket Engine** is our automated IT Service Management system that:\n\n"
                         "• Processes chat conversations to create ServiceNow tickets\n"
                         "• Uses AI to classify requests (incidents vs service requests)\n"
                         "• Automates ticket creation and notifications\n"
                         "• Provides instant responses to common IT questions\n\n"
                         "It's designed to make IT support faster and more efficient!"
            },
            {
                "questions": [
                    "how to raise a ticket",
                    "how to create a ticket",
                    "how to report an issue",
                    "how to request something",
                    "how do i get help"
                ],
                "answer": "📝 **You can raise a ticket in two ways:**\n\n"
                         "1. **Chat with me** - Just describe your issue or request, and I'll help you create a ticket\n"
                         "2. **Email** - Send details to itsupport@payg.com\n\n"
                         "For **urgent issues**, call IT helpdesk: +1-555-IT-HELP (483-4357)"
            },
            {
                "questions": [
                    "what is sla",
                    "service level agreement",
                    "how long for ticket",
                    "response time",
                    "resolution time"
                ],
                "answer": "⏱️ **Service Level Agreements (SLAs):**\n\n"
                         "🔴 **Priority 1 (High)**\n"
                         "   • Response: Within 1 hour\n"
                         "   • Resolution: Within 4 hours\n\n"
                         "🟡 **Priority 2 (Medium)**\n"
                         "   • Response: Within 4 hours\n"
                         "   • Resolution: Within 1 business day\n\n"
                         "🟢 **Priority 3 (Low)**\n"
                         "   • Response: Within 1 business day\n"
                         "   • Resolution: Within 3 business days"
            },
            {
                "questions": [
                    "contact it support",
                    "it helpdesk number",
                    "call it",
                    "it phone number",
                    "it support contact"
                ],
                "answer": "📞 **IT Support Contact Information:**\n\n"
                         "**Phone**: +1-555-IT-HELP (483-4357)\n"
                         "**Email**: itsupport@payg.com\n"
                         "**Hours**: Monday-Friday, 8 AM - 6 PM\n"
                         "**After Hours**: For critical issues only"
            },
            {
                "questions": [
                    "what tickets can i raise",
                    "what issues can i report",
                    "types of tickets",
                    "what can i request"
                ],
                "answer": "🎫 **You can raise these types of tickets:**\n\n"
                         "**🔧 Incidents** (Something is broken):\n"
                         "• Hardware issues (laptop, monitor, keyboard)\n"
                         "• Software problems (login issues, app errors)\n"
                         "• Network issues (WiFi, VPN, internet)\n"
                         "• Email and access problems\n\n"
                         "**📋 Service Requests** (Something you need):\n"
                         "• New hardware (laptop, mouse, monitor)\n"
                         "• Software installation\n"
                         "• Access requests (folders, applications)\n"
                         "• Account setup/modifications"
            },
            {
                "questions": [
                    "what can you do",
                    "your capabilities",
                    "help me with",
                    "what do you do"
                ],
                "answer": "🤖 **I can help you with:**\n\n"
                         "1. **Report IT Issues** - Hardware, software, network problems\n"
                         "2. **Service Requests** - New equipment, software, access\n"
                         "3. **FAQ** - Questions about PayG Ticket Engine and IT processes\n\n"
                         "Just tell me what you need, and I'll guide you through the process!"
            }
        ]
    
    def get_answer(self, question: str) -> str:
        """
        Find the best answer for a question
        """
        question_lower = question.lower().strip()
        
        # Check each FAQ entry
        for faq in self.faq_data:
            for q in faq["questions"]:
                if self._is_similar(question_lower, q):
                    return faq["answer"]
        
        # Default response
        return ("I can answer questions about:\n"
                "• PayG Ticket Engine\n"
                "• How to raise tickets\n"
                "• SLAs and response times\n"
                "• IT support contact info\n"
                "• Types of tickets you can raise\n\n"
                "Please ask a specific question about IT service management.")
    
    def _is_similar(self, question1: str, question2: str) -> bool:
        """
        Simple similarity check
        """
        words1 = set(re.findall(r'\w+', question1))
        words2 = set(re.findall(r'\w+', question2))
        
        if not words1 or not words2:
            return False
        
        common_words = words1.intersection(words2)
        similarity = len(common_words) / max(len(words1), len(words2))
        
        return similarity > 0.4