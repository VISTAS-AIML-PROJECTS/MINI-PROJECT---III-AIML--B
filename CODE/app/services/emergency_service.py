"""
Emergency Alert Service
Handles emergency alerts and SMS notifications
"""

import os
import uuid
import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime


class EmergencyService:
    """
    Manages emergency alerts with SMS delivery tracking
    """

    def __init__(self, db_path: str = 'genvoice.db'):
        self.db_path = db_path
        # SMS credentials (configure when ready)
        self.sms_enabled = False  # Set to True when SMS provider configured


    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def create_alert(self,
                     senior_id: str,
                     conversation_id: Optional[str],
                     alert_type: str,
                     severity: str,
                     trigger_data: str,
                     message: str) -> Dict[str, Any]:
        """
        Create emergency alert and attempt SMS delivery
        Returns: {alert_id, status, sms_sent}
        """

        alert_id = str(uuid.uuid4())
        triggered_at = datetime.now().isoformat()

        conn = self._get_db()
        cursor = conn.cursor()

        # Check for duplicate (rate limiting)
        cursor.execute('''
            SELECT id FROM emergency_alerts
            WHERE senior_id = ? AND status = 'active'
            AND datetime(triggered_at) > datetime('now', '-5 minutes')
        ''', (senior_id,))

        recent_alert = cursor.fetchone()
        if recent_alert:
            conn.close()
            return {
                "success": True,
                "alert_id": recent_alert['id'],
                "status": "duplicate",
                "message": "Alert already created in last 5 minutes"
            }

        # Create alert record
        cursor.execute('''
            INSERT INTO emergency_alerts (
                id, senior_id, alert_type, severity, trigger_data,
                message, triggered_at, delivery_status, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert_id, senior_id, alert_type, severity,
            trigger_data, message, triggered_at,
            'pending', 'active'
        ))

        conn.commit()

        # Get family contacts
        cursor.execute('''
            SELECT phone_number, name FROM family_members
            WHERE senior_id = ? AND is_active = 1
            AND receive_emergencies = 1
            ORDER BY alert_priority ASC
        ''', (senior_id,))

        contacts = [dict(row) for row in cursor.fetchall()]

        # Attempt SMS delivery
        sms_sent = False
        if contacts and self.sms_enabled:
            sms_sent = self._send_sms_alerts(alert_id, contacts, message)

        # Update delivery status
        if sms_sent:
            cursor.execute('''
                UPDATE emergency_alerts
                SET delivery_status = 'sent', notification_sent_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), alert_id))
            conn.commit()

        conn.close()

        return {
            "success": True,
            "alert_id": alert_id,
            "status": "created",
            "sms_sent": sms_sent,
            "contacts_notified": len(contacts) if sms_sent else 0
        }


    def _send_sms_alerts(self, alert_id: str, contacts: list, message: str) -> bool:
        """
        Send SMS to family contacts
        Returns True if at least one SMS sent successfully
        """

        # TODO: Integrate with actual SMS provider (Twilio, AWS SNS, etc)
        # For now, just log the attempt

        print(f"[EMERGENCY] Alert {alert_id}")
        print(f"[EMERGENCY] Message: {message}")
        print(f"[EMERGENCY] Would send to {len(contacts)} contacts")

        for contact in contacts:
            print(f"[EMERGENCY] -> {contact['name']}: {contact['phone_number']}")

        # Return False until SMS is actually configured
        return False


    def get_alerts(self, senior_id: str, status: Optional[str] = None) -> list:
        """Get alerts for a senior"""

        conn = self._get_db()
        cursor = conn.cursor()

        if status:
            cursor.execute('''
                SELECT * FROM emergency_alerts
                WHERE senior_id = ? AND status = ?
                ORDER BY triggered_at DESC
            ''', (senior_id, status))
        else:
            cursor.execute('''
                SELECT * FROM emergency_alerts
                WHERE senior_id = ?
                ORDER BY triggered_at DESC
            ''', (senior_id,))

        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return alerts


    def acknowledge_alert(self, alert_id: str, caregiver_notes: Optional[str] = None) -> bool:
        """Caregiver acknowledges alert"""

        conn = self._get_db()
        cursor = conn.cursor()

        acknowledged_at = datetime.now().isoformat()

        cursor.execute('''
            UPDATE emergency_alerts
            SET caregiver_acknowledged_at = ?, resolution_notes = ?
            WHERE id = ?
        ''', (acknowledged_at, caregiver_notes, alert_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success


    def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Mark alert as resolved"""

        conn = self._get_db()
        cursor = conn.cursor()

        resolved_at = datetime.now().isoformat()

        cursor.execute('''
            UPDATE emergency_alerts
            SET status = 'resolved', resolved_at = ?, resolution_notes = ?
            WHERE id = ?
        ''', (resolved_at, resolution_notes, alert_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success
