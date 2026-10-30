"""
Conversation API Routes
Blueprint-based conversation endpoints
"""

from starlette.responses import JSONResponse
from starlette.requests import Request
import sqlite3
from datetime import datetime

from ..services.conversation_controller import ConversationController


def get_controller():
    """Get controller instance"""
    return ConversationController()


def get_db():
    """Database helper"""
    conn = sqlite3.connect('genvoice.db')
    conn.row_factory = sqlite3.Row
    return conn


async def start_conversation(request: Request):
    """
    POST /api/v1/conversations
    Start a new conversation
    """
    try:
        body = await request.json()
        senior_id = body.get('senior_id')

        if not senior_id:
            return JSONResponse({
                'success': False,
                'error': 'senior_id is required'
            }, status_code=400)

        # Get senior info
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM seniors WHERE id = ?', (senior_id,))
        senior = cursor.fetchone()
        conn.close()

        if not senior:
            return JSONResponse({
                'success': False,
                'error': 'Senior not found'
            }, status_code=404)

        senior_name = senior['name']

        # Start conversation
        result = get_controller().start_conversation(senior_id, senior_name)

        return JSONResponse({
            'success': True,
            'data': result
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


async def submit_message(request: Request):
    """
    POST /api/v1/conversations/{conversation_id}/messages
    Submit user message
    """
    try:
        conversation_id = request.path_params['conversation_id']
        body = await request.json()

        message_id = body.get('message_id')
        text = body.get('text')

        if not message_id or not text:
            return JSONResponse({
                'success': False,
                'error': 'message_id and text are required'
            }, status_code=400)

        # Get senior info
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.name FROM conversations c
            JOIN seniors s ON c.senior_id = s.id
            WHERE c.id = ?
        ''', (conversation_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return JSONResponse({
                'success': False,
                'error': 'Conversation not found'
            }, status_code=404)

        senior_name = result['name']

        # Process message
        result = get_controller().process_message(
            conversation_id,
            message_id,
            text,
            senior_name
        )

        if not result.get('success'):
            status_code = 400 if result.get('sync_status') == 'rejected' else 500
            return JSONResponse(result, status_code=status_code)

        return JSONResponse({
            'success': True,
            'data': result
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


async def get_conversation(request: Request):
    """
    GET /api/v1/conversations/{conversation_id}
    Get conversation details
    """
    try:
        conversation_id = request.path_params['conversation_id']

        result = get_controller().get_conversation_status(conversation_id)

        if not result.get('success'):
            return JSONResponse(result, status_code=404)

        return JSONResponse({
            'success': True,
            'data': result
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


async def get_senior_conversations(request: Request):
    """
    GET /api/v1/seniors/{senior_id}/conversations
    Get conversation history for a senior
    """
    try:
        senior_id = request.path_params['senior_id']

        conn = get_db()
        cursor = conn.cursor()

        # Get conversations
        cursor.execute('''
            SELECT id, senior_id, status, current_state, current_topic,
                   started_at, completed_at
            FROM conversations
            WHERE senior_id = ?
            ORDER BY started_at DESC
            LIMIT 20
        ''', (senior_id,))

        conversations = [dict(row) for row in cursor.fetchall()]

        # Include each transcript and its caregiver-facing summary so the
        # dashboard can show active sessions and completed notes together.
        for conv in conversations:
            cursor.execute('''
                SELECT id, speaker, content, intent, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC, id ASC
            ''', (conv['id'],))
            conv['messages'] = [dict(row) for row in cursor.fetchall()]
            conv['message_count'] = len(conv['messages'])

            cursor.execute('''
                SELECT * FROM summaries
                WHERE conversation_id = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (conv['id'],))
            summary = cursor.fetchone()
            conv['summary'] = dict(summary) if summary else None
            if conv['summary'] and 'caregiver_note' not in conv['summary']:
                conv['summary']['caregiver_note'] = None

        conn.close()

        return JSONResponse({
            'success': True,
            'data': {
                'senior_id': senior_id,
                'conversations': conversations
            }
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


async def get_latest_summary(request: Request):
    """
    GET /api/v1/seniors/{senior_id}/summary/latest
    Get latest conversation summary
    """
    try:
        senior_id = request.path_params['senior_id']

        conn = get_db()
        cursor = conn.cursor()

        # Get latest completed conversation
        cursor.execute('''
            SELECT c.*, s.*
            FROM conversations c
            LEFT JOIN summaries s ON c.id = s.conversation_id
            WHERE c.senior_id = ? AND c.status = 'completed'
            ORDER BY c.completed_at DESC
            LIMIT 1
        ''', (senior_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return JSONResponse({
                'success': True,
                'data': None,
                'message': 'No completed conversations found'
            })

        summary_data = dict(result)

        return JSONResponse({
            'success': True,
            'data': summary_data
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)
