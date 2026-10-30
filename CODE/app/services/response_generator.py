"""
Response Generator Service
Generates empathetic, elderly-friendly responses using LLM
"""

import os
from typing import Dict, Any, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class ResponseGenerator:
    """
    Generates supportive AI responses for elderly users
    - Short, simple language
    - One question at a time
    - Empathetic but not patronizing
    """

    # Fallback responses when LLM unavailable
    FALLBACK_RESPONSES = {
        "POSITIVE": "That's wonderful to hear!",
        "NEGATIVE": "I'm here to listen. Would you like to tell me more?",
        "LONELY": "I understand. Have you been able to speak with anyone today?",
        "PHYSICAL_DISCOMFORT": "I'm sorry to hear that. Would you like me to help you contact your caregiver?",
        "ASSISTANCE_NEEDED": "I'm here to help. What do you need assistance with?",
        "UNCLEAR": "I didn't quite understand. Could you say that in a different way?",
        "SKIP": "No problem. Let's move on to the next question.",
        "OTHER": "I see. Let me ask you something else."
    }

    RESPONSE_PROMPT = """You are a calm, kind, supportive AI companion for an elderly person.

The user just said: "{user_message}"

Their emotional state is: {intent}

Context: {context}

Generate a SHORT, empathetic response (1-2 sentences MAX). Use simple words. Be warm but not patronizing.

Rules:
- Keep it under 20 words
- Use simple, clear language
- Be supportive and kind
- Do NOT ask multiple questions
- Do NOT use complex sentences
- Do NOT be overly cheerful if they're struggling

Respond naturally:"""

    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("[WARNING] GROQ_API_KEY not found, using fallback responses")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self._llm_failed = False


    def generate(self,
                 user_message: str,
                 intent: str,
                 context: Optional[str] = None,
                 next_question: Optional[str] = None) -> str:
        """
        Generate supportive response
        If next_question provided, append it after the supportive statement
        """

        # If no LLM available, use fallback
        if not self.client or self._llm_failed:
            response = self.FALLBACK_RESPONSES.get(intent, "I understand.")
            if next_question:
                return f"{response} {next_question}"
            return response

        try:
            # Generate empathetic acknowledgment
            prompt = self.RESPONSE_PROMPT.format(
                user_message=user_message,
                intent=intent,
                context=context or "This is a daily wellness check-in conversation"
            )

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a supportive AI companion for elderly people. Keep responses SHORT and SIMPLE."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )

            response = completion.choices[0].message.content.strip()

            # Add next question if provided
            if next_question:
                return f"{response} {next_question}"

            return response

        except Exception as e:
            print(f"[ERROR] Response generation failed: {e}")
            if "401" in str(e) or "invalid_api_key" in str(e):
                self._llm_failed = True
            # Fallback
            response = self.FALLBACK_RESPONSES.get(intent, "I understand.")
            if next_question:
                return f"{response} {next_question}"
            return response


    def generate_greeting(self, senior_name: str, time_of_day: str = "morning") -> str:
        """Generate personalized greeting"""

        greetings = {
            "morning": f"Good morning, {senior_name}! How are you feeling today?",
            "afternoon": f"Good afternoon, {senior_name}! How are you feeling today?",
            "evening": f"Good evening, {senior_name}! How are you feeling today?"
        }

        return greetings.get(time_of_day, f"Hello, {senior_name}! How are you feeling today?")


    def generate_closing(
        self,
        senior_name: str,
        wellness_status: str,
        note_shared: bool = False
    ) -> str:
        """Generate conversation closing"""

        if note_shared:
            return (
                f"Thank you, {senior_name}. I have added your note to the summary "
                "for your caregiver. Take care!"
            )

        if wellness_status == "good":
            return f"Thank you, {senior_name}! You're doing great today. Take care!"

        elif wellness_status == "fair":
            return f"Thank you for checking in, {senior_name}. Your caregiver will be updated. Take care!"

        else:  # concerning
            return f"Thank you, {senior_name}. I've noted your concerns and your caregiver will be notified right away. Please reach out if you need anything."
