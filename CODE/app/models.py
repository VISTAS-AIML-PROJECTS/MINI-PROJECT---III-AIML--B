"""
GenVoice 2.0 - Database Models

SQLAlchemy ORM models for all database tables
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Time, Text, ForeignKey, JSON
# Note: Using JSON instead of JSONB for SQLite compatibility
# Note: ARRAY not available in SQLite, we'll use JSON to store arrays
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, time as time_type
import uuid

from .database import Base


# Helper function for UUID
def generate_uuid():
    return str(uuid.uuid4())


class Senior(Base):
    """Elderly user profile"""
    __tablename__ = "seniors"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    date_of_birth = Column(Date, nullable=True)
    timezone = Column(String(50), default="America/New_York")

    # Check-in schedule
    check_in_morning_time = Column(Time, default=time_type(8, 0, 0))
    check_in_evening_time = Column(Time, default=time_type(19, 0, 0))

    # Emergency settings (stored as JSON since SQLite doesn't support ARRAY)
    emergency_keywords = Column(Text, default='["help", "emergency", "fallen", "pain"]')

    # Voice settings
    voice_speed = Column(Float, default=0.85)  # 0.85x for elderly

    # Status
    created_at = Column(DateTime, default=func.now())
    last_check_in = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    family_members = relationship("FamilyMember", back_populates="senior", cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", back_populates="senior", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="senior", cascade="all, delete-orphan")
    medication_logs = relationship("MedicationLog", back_populates="senior", cascade="all, delete-orphan")
    emergency_alerts = relationship("EmergencyAlert", back_populates="senior", cascade="all, delete-orphan")


class FamilyMember(Base):
    """Family contact who receives alerts"""
    __tablename__ = "family_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    senior_id = Column(String, ForeignKey("seniors.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    relationship_type = Column(String(50), nullable=True)  # daughter, son, spouse
    phone_number = Column(String(20), nullable=False, index=True)
    email = Column(String(100), nullable=True)

    # Alert settings
    alert_priority = Column(Integer, default=1)  # 1=primary, 2=secondary
    receive_daily_updates = Column(Boolean, default=True)
    receive_warnings = Column(Boolean, default=True)
    receive_emergencies = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    senior = relationship("Senior", back_populates="family_members")


class CheckIn(Base):
    """Daily check-in conversation record"""
    __tablename__ = "check_ins"

    id = Column(String, primary_key=True, default=generate_uuid)
    senior_id = Column(String, ForeignKey("seniors.id", ondelete="CASCADE"), nullable=False, index=True)

    check_in_type = Column(String(20), nullable=False)  # morning, evening
    scheduled_time = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)

    # Conversation data
    conversation_transcript = Column(Text, nullable=True)

    # AI analysis results
    wellness_status = Column(String(20), nullable=True)  # good, fair, poor, concerning
    wellness_score = Column(Integer, nullable=True)  # 1-10
    concerns_detected = Column(Text, nullable=True)  # JSON string: ["knee pain", "fatigue"]
    concern_severity = Column(Integer, nullable=True)  # 1-10
    ai_summary = Column(Text, nullable=True)

    status = Column(String(20), default='pending', index=True)  # pending, completed, missed, skipped
    created_at = Column(DateTime, default=func.now())

    # Relationships
    senior = relationship("Senior", back_populates="check_ins")


class Medication(Base):
    """Medication schedule for senior"""
    __tablename__ = "medications"

    id = Column(String, primary_key=True, default=generate_uuid)
    senior_id = Column(String, ForeignKey("seniors.id", ondelete="CASCADE"), nullable=False, index=True)

    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=True)
    instructions = Column(Text, nullable=True)

    # Schedule - stored as JSON for SQLite compatibility
    scheduled_times = Column(Text, nullable=False)  # JSON: ["08:00:00", "20:00:00"]
    days_of_week = Column(Text, default='[0,1,2,3,4,5,6]')  # JSON: [0,1,2,3,4,5,6] (0=Sun)

    start_date = Column(Date, default=func.current_date())
    end_date = Column(Date, nullable=True)

    reminder_before_minutes = Column(Integer, default=5)
    is_critical = Column(Boolean, default=False)  # Critical meds flag missed doses

    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    senior = relationship("Senior", back_populates="medications")
    medication_logs = relationship("MedicationLog", back_populates="medication", cascade="all, delete-orphan")


class MedicationLog(Base):
    """Medication compliance tracking"""
    __tablename__ = "medication_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    medication_id = Column(String, ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    senior_id = Column(String, ForeignKey("seniors.id", ondelete="CASCADE"), nullable=False, index=True)

    scheduled_time = Column(DateTime, nullable=False, index=True)
    taken_at = Column(DateTime, nullable=True)

    status = Column(String(20), nullable=False, index=True)  # taken, missed, skipped, pending
    confirmation_method = Column(String(20), nullable=True)  # voice, button, manual
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    medication = relationship("Medication", back_populates="medication_logs")
    senior = relationship("Senior", back_populates="medication_logs")


class EmergencyAlert(Base):
    """Emergency event tracking"""
    __tablename__ = "emergency_alerts"

    id = Column(String, primary_key=True, default=generate_uuid)
    senior_id = Column(String, ForeignKey("seniors.id", ondelete="CASCADE"), nullable=False, index=True)

    alert_type = Column(String(50), nullable=False)  # emergency_keyword, emergency_button, missed_checkin, medication_missed
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical

    # Event data (stored as JSON for flexibility)
    trigger_data = Column(Text, nullable=True)  # JSON string
    conversation_context = Column(Text, nullable=True)

    # Timing
    triggered_at = Column(DateTime, default=func.now(), index=True)
    family_notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    family_response_time = Column(Integer, nullable=True)  # seconds

    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    status = Column(String(20), default='active', index=True)  # active, resolved, false_alarm

    # Relationships
    senior = relationship("Senior", back_populates="emergency_alerts")
