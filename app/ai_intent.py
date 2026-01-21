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
  "intent": string,
  "category": string,
  "subcategory": string,
  "priority": "low" | "medium" | "high",
  "ticket_required": boolean,
  "confidence": number,
  "short_description": string
}
"""


def detect_intent(email_text: str):
    print(f"detect intent triggered---------------------------------------------------------------------------------------------: {email_text}")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": email_text}
        ],
        temperature=0
    )

    return response.choices[0].message.content