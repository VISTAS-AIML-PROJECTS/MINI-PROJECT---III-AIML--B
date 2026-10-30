"""
Conversation Service
Handles conversation persistence with idempotent message storage
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


class ConversationService:
    """
    Manages conversation and message persistence
    Ensures idempotency using client-generated message_id
    """

    def __init__(self, db_path: str = 'genvoice.db'):
        self.db_path = db_path


    def _get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def create_conversation(self, senior_id: str) -> Dict[str, Any]:
        """
        Create new conversation session
        Returns conversation_id and initial state
        """
        conversation_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO conversations (id, senior_id, status, current_state, started_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (conversation_id, senior_id, 'active', 'IDLE', started_at))

        conn.commit()
        conn.close()

        return {
            "conversation_id": conversation_id,
            "senior_id": senior_id,
            "status": "active",
            "current_state": "IDLE",
            "started_at": started_at
        }


    def save_message(self,
                     conversation_id: str,
                     message_id: str,
                     speaker: str,
                     content: str,
                     intent: Optional[str] = None,
                     confidence: Optional[float] = None) -> Dict[str, Any]:
        """
        Save message with idempotency
        Returns: {success, message, duplicate}
        """

        conn = self._get_db()
        cursor = conn.cursor()

        try:
            # Check if message_id already exists (idempotency check)
            cursor.execute('SELECT id, content FROM messages WHERE message_id = ?', (message_id,))
            existing = cursor.fetchone()

            if existing:
                conn.close()
                return {
                    "success": True,
                    "message": "Message already exists (idempotent)",
                    "duplicate": True,
                    "message_db_id": existing['id']
                }

            # Insert new message
            created_at = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO messages (conversation_id, message_id, speaker, content, intent, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (conversation_id, message_id, speaker, content, intent, confidence, created_at))

            message_db_id = cursor.lastrowid

            conn.commit()
            conn.close()

            return {
                "success": True,
                "message": "Message saved",
                "duplicate": False,
                "message_db_id": message_db_id
            }

        except sqlite3.IntegrityError as e:
            # Unique constraint violation - message_id already exists
            conn.close()
            return {
                "success": True,
                "message": "Message already exists (constraint)",
                "duplicate": True
            }

        except Exception as e:
            conn.close()
            return {
                "success": False,
                "message": f"Failed to save message: {str(e)}",
                "duplicate": False
            }


    def update_conversation_state(self,
                                  conversation_id: str,
                                  current_state: str,
                                  current_topic: Optional[str] = None,
                                  status: Optional[str] = None,
                                  state_data: Optional[str] = None,
                                  completed_states: Optional[str] = None) -> bool:
        """
        Update conversation state
        Returns True if successful
        """

        conn = self._get_db()
        cursor = conn.cursor()

        try:
            updates = ["current_state = ?"]
            params = [current_state]

            if current_topic is not None:
                updates.append("current_topic = ?")
                params.append(current_topic)

            if status is not None:
                updates.append("status = ?")
                params.append(status)

                # Set completed_at if status is completed
                if status == "completed":
                    updates.append("completed_at = ?")
                    params.append(datetime.now().isoformat())

            if state_data is not None:
                updates.append("state_data = ?")
                params.append(state_data)

            if completed_states is not None:
                updates.append("completed_states = ?")
                params.append(completed_states)

            params.append(conversation_id)

            query = f"UPDATE conversations SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"[ERROR] Failed to update conversation state: {e}")
            conn.close()
            return False


    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM conversations WHERE id = ?', (conversation_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)


    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        ''', (conversation_id,))

        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return messages


    def get_latest_conversation(self, senior_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent active conversation for a senior"""

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM conversations
            WHERE senior_id = ? AND status = 'active'
            ORDER BY started_at DESC LIMIT 1
        ''', (senior_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)


    def get_conversation_history(self, senior_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a senior"""

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM conversations
            WHERE senior_id = ?
            ORDER BY started_at DESC LIMIT ?
        ''', (senior_id, limit))

        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return conversations


    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if conversation exists"""

        conn = self._get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM conversations WHERE id = ?', (conversation_id,))
        exists = cursor.fetchone() is not None
        conn.close()

        return exists
