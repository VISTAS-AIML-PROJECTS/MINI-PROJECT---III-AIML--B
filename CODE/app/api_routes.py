"""
Blueprint API Routes - MVP Endpoints
Simple conversation endpoints for senior app and caregiver dashboard
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid

from .services.conversation_controller import ConversationController
from .services.conversation_service import ConversationService
from .services.summary_generator import SummaryGenerator

router = APIRouter()

# Initialize services
conversation_controller = ConversationController()
conversation_service = ConversationService()
summary_generator = SummaryGenerator()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class StartConversationRequest(BaseModel):
    senior_id: str
    senior_name: str


class SendMessageRequest(BaseModel):
    message_id: str
    text: str
    senior_name: str


# ============================================
# CONVERSATION ENDPOINTS
# ============================================

@router.post("/conversations")
async def start_conversation(request: StartConversationRequest):
    """Start a new conversation with a senior"""
    try:
        result = conversation_controller.start_conversation(
            request.senior_id,
            request.senior_name
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """Send a message in a conversation"""
    try:
        result = conversation_controller.process_message(
            conversation_id,
            request.message_id,
            request.text,
            request.senior_name
        )

        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to process message"))

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details with messages"""
    try:
        result = conversation_controller.get_conversation_status(conversation_id)

        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seniors/{senior_id}/conversations")
async def get_senior_conversations(senior_id: str, limit: int = 10):
    """Get all conversations for a senior"""
    try:
        conversations = conversation_service.get_conversation_history(senior_id, limit)

        # Enrich each conversation with message count
        for conv in conversations:
            messages = conversation_service.get_messages(conv["id"])
            conv["message_count"] = len(messages)

            # Get last message
            if messages:
                last_msg = messages[-1]
                conv["last_message"] = {
                    "speaker": last_msg["speaker"],
                    "content": last_msg["content"][:100],  # First 100 chars
                    "created_at": last_msg["created_at"]
                }

        return {
            "success": True,
            "data": {
                "conversations": conversations,
                "count": len(conversations)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seniors/{senior_id}/conversations/latest")
async def get_latest_conversation(senior_id: str):
    """Get the latest active conversation for a senior"""
    try:
        conversation = conversation_service.get_latest_conversation(senior_id)

        if not conversation:
            return {
                "success": True,
                "data": None
            }

        # Get messages
        messages = conversation_service.get_messages(conversation["id"])

        return {
            "success": True,
            "data": {
                "conversation": conversation,
                "messages": messages
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seniors/{senior_id}/dashboard")
async def get_dashboard(senior_id: str):
    """
    Dashboard endpoint for caregiver app.
    Returns: recent conversations with summaries + messages.
    """
    try:
        import sqlite3
        conn = sqlite3.connect("genvoice.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get recent conversations (latest 10)
        cursor.execute('''
            SELECT * FROM conversations
            WHERE senior_id = ?
            ORDER BY started_at DESC LIMIT 10
        ''', (senior_id,))
        conversations = [dict(row) for row in cursor.fetchall()]

        dashboard_conversations = []

        for conv in conversations:
            conv_id = conv["id"]

            # Get messages
            cursor.execute('''
                SELECT speaker, content, intent, created_at
                FROM messages WHERE conversation_id = ?
                ORDER BY created_at ASC
            ''', (conv_id,))
            messages = [dict(row) for row in cursor.fetchall()]

            # Get summary if exists
            cursor.execute('''
                SELECT summary_text, self_reported_mood, sleep_response,
                       meals_response, social_connection_response,
                       assistance_needed, assistance_details,
                       potential_urgent_concern, conversation_status
                FROM summaries WHERE conversation_id = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (conv_id,))
            summary_row = cursor.fetchone()
            summary = dict(summary_row) if summary_row else None

            dashboard_conversations.append({
                "id": conv_id,
                "status": conv["status"],
                "current_state": conv["current_state"],
                "started_at": conv["started_at"],
                "completed_at": conv.get("completed_at"),
                "message_count": len(messages),
                "messages": messages,
                "summary": summary
            })

        conn.close()

        return {
            "success": True,
            "data": {
                "senior_id": senior_id,
                "conversations": dashboard_conversations,
                "total": len(dashboard_conversations)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
