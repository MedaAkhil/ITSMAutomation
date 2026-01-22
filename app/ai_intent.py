import json
import os
from groq import Groq

client = Groq(api_key="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")

SYSTEM_PROMPT = """
You are an ITSM intent classification engine.

STRICT RULES:
- Return ONLY valid JSON
- No explanations
- No markdown
- No HTML
- No text outside JSON

Schema:
{
    "intent_type: incident | service_request | ignore",
    "category: string",
    "subcategory: string",
    "short_description: string",
    "priority: low | medium | high"
}
"""


def detect_intent(email_text: str):
    print(f"\n{'='*80}")
    print("[LLM INTENT DETECTION] Starting...")
    print(f"[INPUT TEXT LENGTH]: {len(email_text)} characters")
    print(f"[INPUT TEXT]: {email_text[:200]}...")
    print(f"{'='*80}\n")
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": email_text}
            ],
            temperature=0
        )
        
        llm_response = response.choices[0].message.content
        print(f"[LLM RAW RESPONSE]: {llm_response}")
        
        parsed = json.loads(llm_response)
        print(f"[LLM PARSED RESPONSE]: {parsed}")
        print(f"{'='*80}\n")
        
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"[LLM JSON ERROR] Failed to parse LLM response: {e}")
        print(f"[RAW RESPONSE]: {llm_response}")
        return {"intent_type": "ignore", "error": "JSON parse failed"}
    except Exception as e:
        print(f"[LLM GENERAL ERROR] {e}")
        return {"intent_type": "ignore", "error": str(e)}