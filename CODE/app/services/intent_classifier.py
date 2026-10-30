"""
Intent Classifier Service
Classifies user responses into predefined intent categories using LLM
"""

import json
import os
from typing import Dict, Any, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class IntentClassifier:
    """
    Classifies user messages into intents using Groq LLM
    Intent allowlist: POSITIVE, NEGATIVE, LONELY, PHYSICAL_DISCOMFORT,
                      ASSISTANCE_NEEDED, URGENT_SYMPTOM, UNCLEAR, SKIP, OTHER
    """

    ALLOWED_INTENTS = [
        "POSITIVE",
        "NEGATIVE",
        "LONELY",
        "PHYSICAL_DISCOMFORT",
        "ASSISTANCE_NEEDED",
        "URGENT_SYMPTOM",
        "UNCLEAR",
        "SKIP",
        "OTHER"
    ]

    CLASSIFICATION_PROMPT = """You are analyzing responses from elderly users during a wellness check-in.

Classify the user's response into EXACTLY ONE of these intents:

- POSITIVE: User is feeling good, happy, fine, well
- NEGATIVE: User is feeling sad, depressed, upset, bad (but NOT physical symptoms)
- LONELY: User mentions being alone, lonely, missing people, no visitors
- PHYSICAL_DISCOMFORT: User mentions non-urgent physical issues (tired, sore, ache, minor pain)
- ASSISTANCE_NEEDED: User explicitly asks for help or mentions needing something
- URGENT_SYMPTOM: Serious symptoms like severe chest pain, can't breathe, stroke symptoms, severe bleeding
- UNCLEAR: Cannot understand the response, too vague, gibberish
- SKIP: User wants to skip the question or not answer
- OTHER: Response is off-topic or doesn't fit any category

CRITICAL: If ANY potentially life-threatening symptom is mentioned (chest pain, breathing difficulty, severe head injury, stroke signs), classify as URGENT_SYMPTOM.

User's response: "{user_message}"

Respond with ONLY valid JSON in this exact format:
{{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "evidence": "brief reason",
  "needs_assistance": false,
  "urgent": false
}}"""

    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("[WARNING] GROQ_API_KEY not found, using fallback classification")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.confidence_threshold = 0.7
        self._llm_failed = False


    def classify(self, user_message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify user message into intent
        Returns: {intent, confidence, evidence, needs_assistance, urgent}
        """

        # Empty message
        if not user_message or not user_message.strip():
            return {
                "intent": "UNCLEAR",
                "confidence": 1.0,
                "evidence": "Empty message",
                "needs_assistance": False,
                "urgent": False
            }

        # Skip LLM if no client or if it already failed (bad key)
        if not self.client or self._llm_failed:
            return self._fallback_classification(user_message)

        try:
            # Call LLM for classification
            prompt = self.CLASSIFICATION_PROMPT.format(user_message=user_message)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON
            result = json.loads(result_text)

            # Validate intent
            intent = result.get("intent", "OTHER")
            if intent not in self.ALLOWED_INTENTS:
                print(f"[WARNING] Invalid intent '{intent}', defaulting to OTHER")
                intent = "OTHER"

            # Validate confidence
            confidence = float(result.get("confidence", 0.5))
            if confidence < 0 or confidence > 1:
                confidence = 0.5

            # If confidence too low, mark as UNCLEAR
            if confidence < self.confidence_threshold and intent not in ["URGENT_SYMPTOM"]:
                intent = "UNCLEAR"
                evidence = f"Low confidence ({confidence:.2f})"
            else:
                evidence = result.get("evidence", "")

            return {
                "intent": intent,
                "confidence": confidence,
                "evidence": evidence,
                "needs_assistance": result.get("needs_assistance", False),
                "urgent": result.get("urgent", False) or intent == "URGENT_SYMPTOM"
            }

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM JSON: {e}")
            return self._fallback_classification(user_message)

        except Exception as e:
            print(f"[ERROR] Intent classification failed: {e}")
            if "401" in str(e) or "invalid_api_key" in str(e):
                self._llm_failed = True
                print("[WARNING] Groq API key invalid, switching to fallback permanently")
            return self._fallback_classification(user_message)


    def _fallback_classification(self, user_message: str) -> Dict[str, Any]:
        """
        Fallback keyword-based classification when LLM fails
        """
        text = user_message.lower().strip()

        # Check for urgent keywords first
        urgent_keywords = ["chest pain", "can't breathe", "cannot breathe", "severe pain",
                           "bleeding heavily", "stroke", "heart attack", "choking"]
        if any(keyword in text for keyword in urgent_keywords):
            return {
                "intent": "URGENT_SYMPTOM",
                "confidence": 0.9,
                "evidence": "Urgent keyword detected",
                "needs_assistance": True,
                "urgent": True
            }

        # Check for assistance keywords
        help_keywords = ["help me", "need help", "can you help", "assist", "need something"]
        if any(keyword in text for keyword in help_keywords):
            return {
                "intent": "ASSISTANCE_NEEDED",
                "confidence": 0.8,
                "evidence": "Help keyword detected",
                "needs_assistance": True,
                "urgent": False
            }

        # Check for lonely keywords (more specific)
        lonely_keywords = ["feel lonely", "feeling lonely", "i'm lonely", "so lonely", "very lonely", "feel alone", "feeling alone", "no one to talk", "nobody to talk", "haven't talked to anyone", "haven't spoken to anyone", "miss my family", "miss my friends"]
        if any(keyword in text for keyword in lonely_keywords):
            return {
                "intent": "LONELY",
                "confidence": 0.7,
                "evidence": "Loneliness keyword detected",
                "needs_assistance": False,
                "urgent": False
            }

        # Check for pain/discomfort
        pain_keywords = ["pain", "hurts", "hurting", "ache", "aching", "sore", "tired", "fatigue", "dizzy", "weak"]
        if any(keyword in text for keyword in pain_keywords):
            return {
                "intent": "PHYSICAL_DISCOMFORT",
                "confidence": 0.7,
                "evidence": "Physical discomfort keyword detected",
                "needs_assistance": False,
                "urgent": False
            }

        # Check for negative mood
        negative_keywords = ["bad", "terrible", "awful", "not good", "not well", "sad", "depressed", "upset", "worried", "anxious"]
        if any(keyword in text for keyword in negative_keywords):
            return {
                "intent": "NEGATIVE",
                "confidence": 0.7,
                "evidence": "Negative mood keyword detected",
                "needs_assistance": False,
                "urgent": False
            }

        # Check for positive (be more specific)
        if any(word in text.split() for word in ["yes", "yeah", "yep", "sure", "okay", "ok"]):
            return {
                "intent": "POSITIVE",
                "confidence": 0.6,
                "evidence": "Affirmative response detected",
                "needs_assistance": False,
                "urgent": False
            }

        # Check for positive mood phrases
        positive_keywords = ["feel good", "feeling good", "feel great", "feeling great", "feel fine", "feeling fine", "feel well", "feeling well", "happy", "wonderful"]
        if any(keyword in text for keyword in positive_keywords):
            return {
                "intent": "POSITIVE",
                "confidence": 0.7,
                "evidence": "Positive mood keyword detected",
                "needs_assistance": False,
                "urgent": False
            }

        # Check for skip
        skip_keywords = ["skip", "don't want", "pass", "next"]
        if any(keyword in text for keyword in skip_keywords):
            return {
                "intent": "SKIP",
                "confidence": 0.8,
                "evidence": "Skip keyword detected",
                "needs_assistance": False,
                "urgent": False
            }

        # Default to UNCLEAR
        return {
            "intent": "UNCLEAR",
            "confidence": 0.5,
            "evidence": "No clear intent detected (fallback)",
            "needs_assistance": False,
            "urgent": False
        }
