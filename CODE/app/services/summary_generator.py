"""
Summary Generator Service
Generates factual conversation summaries using LLM
"""

import os
import json
import uuid
import sqlite3
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class SummaryGenerator:
    """
    Generates structured summaries from conversation messages
    Distinguishes self-reported facts from AI interpretation
    """

    SUMMARY_PROMPT = """You are analyzing a wellness check-in conversation with an elderly person.

Generate a factual summary based on the conversation below.

CONVERSATION:
{conversation}

Generate a JSON summary with these fields:

{{
  "summary_text": "Brief 2-3 sentence summary of the conversation",
  "self_reported_mood": "What they said about mood (or null)",
  "sleep_response": "What they said about sleep (or null)",
  "meals_response": "What they said about meals (or null)",
  "social_connection_response": "What they said about social connection (or null)",
  "assistance_needed": true/false,
  "assistance_details": "What help they need (or null)",
  "caregiver_note": "The senior's final note for their caregiver (or null)",
  "potential_urgent_concern": "Any urgent symptoms mentioned (or null)",
  "overall_wellness": "good/fair/concerning"
}}

CRITICAL:
- Only include what they ACTUALLY said, never invent
- Use null for questions they didn't answer
- Be factual, not interpretive
- Flag urgent concerns clearly

Respond with ONLY valid JSON:"""

    def __init__(self, db_path: str = 'genvoice.db'):
        self.db_path = db_path
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("[WARNING] GROQ_API_KEY not found, summaries will be basic")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"


    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def generate_summary(
        self,
        conversation_id: str,
        caregiver_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate summary for a completed conversation
        Returns: {success, summary_id, summary_data}
        """

        # Get conversation and messages
        conn = self._get_db()
        cursor = conn.cursor()

        # Upgrade existing local databases lazily, without touching conversation data.
        cursor.execute("PRAGMA table_info(summaries)")
        summary_columns = {row[1] for row in cursor.fetchall()}
        if "caregiver_note" not in summary_columns:
            cursor.execute("ALTER TABLE summaries ADD COLUMN caregiver_note TEXT")
            conn.commit()

        cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
        conversation = cursor.fetchone()

        if not conversation:
            conn.close()
            return {"success": False, "error": "Conversation not found"}

        cursor.execute('''
            SELECT speaker, content, intent FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        ''', (conversation_id,))
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not messages:
            return {"success": False, "error": "No messages found"}

        # Build conversation text
        conversation_text = "\n".join([
            f"{msg['speaker'].upper()}: {msg['content']}"
            for msg in messages
        ])

        # Generate summary with LLM
        if self.client:
            try:
                summary_data = self._generate_with_llm(conversation_text)
            except Exception as e:
                print(f"[ERROR] LLM summary failed: {e}")
                summary_data = self._generate_basic_summary(messages)
        else:
            summary_data = self._generate_basic_summary(messages)

        summary_data["caregiver_note"] = caregiver_note
        if caregiver_note:
            note_line = f"Additional note for caregiver: {caregiver_note}"
            summary_text = summary_data.get("summary_text") or "Wellness check-in completed."
            if note_line not in summary_text:
                summary_data["summary_text"] = f"{summary_text.rstrip()} {note_line}"

        # Save summary to database
        summary_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO summaries (
                id, conversation_id, summary_text,
                self_reported_mood, sleep_response, meals_response,
                social_connection_response, assistance_needed,
                assistance_details, caregiver_note, potential_urgent_concern,
                conversation_status, review_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            summary_id,
            conversation_id,
            summary_data["summary_text"],
            summary_data.get("self_reported_mood"),
            summary_data.get("sleep_response"),
            summary_data.get("meals_response"),
            summary_data.get("social_connection_response"),
            1 if summary_data.get("assistance_needed") else 0,
            summary_data.get("assistance_details"),
            caregiver_note,
            summary_data.get("potential_urgent_concern"),
            summary_data.get("overall_wellness", "fair"),
            "pending",
            created_at
        ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "summary_id": summary_id,
            "summary_data": summary_data
        }


    def _generate_with_llm(self, conversation_text: str) -> Dict[str, Any]:
        """Generate summary using LLM"""

        prompt = self.SUMMARY_PROMPT.format(conversation=conversation_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a medical summary assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=400
        )

        result_text = response.choices[0].message.content.strip()
        summary_data = json.loads(result_text)

        return summary_data


    def _generate_basic_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback basic summary when LLM unavailable"""

        user_messages = [msg for msg in messages if msg['speaker'] == 'user']
        intents = [msg.get('intent') for msg in user_messages if msg.get('intent')]

        # Determine wellness
        if 'URGENT_SYMPTOM' in intents:
            overall_wellness = "concerning"
            urgent_concern = "Urgent symptom reported"
        elif 'NEGATIVE' in intents or 'LONELY' in intents or 'PHYSICAL_DISCOMFORT' in intents:
            overall_wellness = "fair"
            urgent_concern = None
        else:
            overall_wellness = "good"
            urgent_concern = None

        assistance_needed = 'ASSISTANCE_NEEDED' in intents
        assistance_details = next(
            (msg['content'] for msg in user_messages if msg.get('intent') == 'ASSISTANCE_NEEDED'),
            None
        )
        reported_concerns = [
            msg['content'] for msg in user_messages
            if msg.get('intent') in {'NEGATIVE', 'LONELY', 'PHYSICAL_DISCOMFORT', 'ASSISTANCE_NEEDED'}
        ]
        summary_text = f"Completed check-in with {len(user_messages)} responses. Overall status: {overall_wellness}."
        if reported_concerns:
            summary_text += " Reported concerns: " + "; ".join(reported_concerns) + "."

        return {
            "summary_text": summary_text,
            "self_reported_mood": None,
            "sleep_response": None,
            "meals_response": None,
            "social_connection_response": None,
            "assistance_needed": assistance_needed,
            "assistance_details": assistance_details,
            "potential_urgent_concern": urgent_concern,
            "overall_wellness": overall_wellness
        }


    def get_summary(self, summary_id: str) -> Optional[Dict[str, Any]]:
        """Get summary by ID"""

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM summaries WHERE id = ?', (summary_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)
