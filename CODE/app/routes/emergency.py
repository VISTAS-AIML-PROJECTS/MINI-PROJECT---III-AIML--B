"""
Emergency Alert API Routes
"""

from starlette.responses import JSONResponse
from starlette.requests import Request
import sqlite3

from ..services.emergency_service import EmergencyService


emergency_service = EmergencyService()


def get_db():
    conn = sqlite3.connect('genvoice.db')
    conn.row_factory = sqlite3.Row
    return conn


async def create_emergency_alert(request: Request):
    """
    POST /api/v1/seniors/{senior_id}/emergency
    Create emergency alert (from button or urgent symptom)
    """
    try:
        senior_id = request.path_params['senior_id']
        body = await request.json()

        alert_type = body.get('alert_type', 'button_press')
        trigger_data = body.get('trigger_data', '')
        conversation_id = body.get('conversation_id')

        # Get senior name
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

        # Determine severity and message
        if alert_type == 'urgent_symptom':
            severity = 'critical'
            message = f"URGENT: {senior_name} reported serious symptoms. Please check on them immediately."
        else:
            severity = 'high'
            message = f"Emergency assistance requested by {senior_name}. Please check on them immediately."

        # Create alert
        result = emergency_service.create_alert(
            senior_id,
            conversation_id,
            alert_type,
            severity,
            trigger_data,
            message
        )

        return JSONResponse({
            'success': True,
            'data': result
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


async def get_alerts(request: Request):
    """
    GET /api/v1/seniors/{senior_id}/alerts
    Get alert history
    """
    try:
        senior_id = request.path_params['senior_id']
        status = request.query_params.get('status')

        alerts = emergency_service.get_alerts(senior_id, status)

        return JSONResponse({
            'success': True,
            'data': {
                'senior_id': senior_id,
                'alerts': alerts,
                'count': len(alerts)
            }
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


async def acknowledge_alert(request: Request):
    """
    PATCH /api/v1/alerts/{alert_id}/acknowledge
    Caregiver acknowledges alert
    """
    try:
        alert_id = request.path_params['alert_id']
        body = await request.json()

        notes = body.get('notes', '')

        success = emergency_service.acknowledge_alert(alert_id, notes)

        if not success:
            return JSONResponse({
                'success': False,
                'error': 'Alert not found'
            }, status_code=404)

        return JSONResponse({
            'success': True,
            'message': 'Alert acknowledged'
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)


async def resolve_alert(request: Request):
    """
    PATCH /api/v1/alerts/{alert_id}/resolve
    Mark alert as resolved
    """
    try:
        alert_id = request.path_params['alert_id']
        body = await request.json()

        notes = body.get('notes', 'Resolved')

        success = emergency_service.resolve_alert(alert_id, notes)

        if not success:
            return JSONResponse({
                'success': False,
                'error': 'Alert not found'
            }, status_code=404)

        return JSONResponse({
            'success': True,
            'message': 'Alert resolved'
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=500)
