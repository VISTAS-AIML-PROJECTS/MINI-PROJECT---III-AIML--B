package com.genvoice.caregiver.utils

/**
 * Application constants and configuration
 */
object Constants {

    // ==================== API CONFIGURATION ====================

    /**
     * Backend API Base URL
     * - Emulator: Use 10.0.2.2 (maps to host's localhost)
     * - Real Device: Use computer's local IP (e.g., 192.168.1.100)
     * - Production: Use deployed URL
     */
    const val BASE_URL = "http://127.0.0.1:8000"  // USB - Keep cable connected
    const val API_BASE_URL = BASE_URL  // Alias for consistency

    /**
     * API Endpoints
     */
    object Endpoints {
        const val HEALTH = "health"
        const val SENIORS = "api/v1/seniors"
        const val SENIOR_DETAIL = "api/v1/seniors/{id}"
        const val SENIOR_DASHBOARD = "api/v1/seniors/{id}/dashboard"
        const val CHECKIN_START = "api/v1/checkin/start"
        const val CHECKIN_SUBMIT = "api/v1/checkin/submit"
        const val SENIOR_CHECKINS = "api/v1/seniors/{id}/checkins"
        const val MEDICATIONS = "api/v1/medications"
        const val SENIOR_MEDICATIONS = "api/v1/seniors/{id}/medications"
        const val MEDICATION_TAKEN = "api/v1/medications/taken"
        const val MEDICATION_LOGS = "api/v1/medications/{id}/logs"
        const val EMERGENCY_ALERT = "api/v1/emergency/alert"
        const val SENIOR_EMERGENCIES = "api/v1/seniors/{id}/emergencies"
    }

    // ==================== DEMO DATA ====================

    /**
     * Hardcoded demo senior ID for testing
     * Margaret Johnson from database
     */
    const val DEMO_SENIOR_ID = "8e863196-9110-4a6e-89c0-f3ef0c16179d"

    /**
     * Demo medication ID
     */
    const val DEMO_MEDICATION_ID = "82127a04-b311-4205-8c18-06e423fdb9e0"

    /**
     * Demo senior name
     */
    const val DEMO_SENIOR_NAME = "Margaret"

    /**
     * Demo senior full name
     */
    const val DEMO_SENIOR_FULL_NAME = "Margaret Johnson"

    // ==================== VOICE SETTINGS ====================

    /**
     * Text-to-Speech speed (0.85 = 15% slower for elderly)
     */
    const val TTS_SPEED = 0.85f

    /**
     * Text-to-Speech pitch (normal)
     */
    const val TTS_PITCH = 1.0f

    /**
     * Speech-to-Text timeout in milliseconds (7 seconds of silence)
     * Balanced for elderly speech while preventing long waits
     */
    const val STT_TIMEOUT_MS = 7000L

    /**
     * Maximum speech recognition duration (30 seconds)
     */
    const val STT_MAX_DURATION_MS = 30000L

    // ==================== CHECK-IN SETTINGS ====================

    /**
     * Morning check-in time (8:00 AM)
     */
    const val MORNING_CHECKIN_HOUR = 8
    const val MORNING_CHECKIN_MINUTE = 0

    /**
     * Evening check-in time (7:00 PM)
     */
    const val EVENING_CHECKIN_HOUR = 19
    const val EVENING_CHECKIN_MINUTE = 0

    /**
     * Check-in types
     */
    object CheckInType {
        const val MORNING = "morning"
        const val EVENING = "evening"
        const val MANUAL = "manual"
    }

    // ==================== EMERGENCY SETTINGS ====================

    /**
     * Emergency keywords that trigger alert
     */
    val EMERGENCY_KEYWORDS = listOf(
        "help",
        "emergency",
        "fallen",
        "fell",
        "pain",
        "hurt",
        "sick",
        "dizzy",
        "can't breathe",
        "chest pain",
        "ambulance",
        "911"
    )

    /**
     * Emergency severity levels
     */
    object EmergencySeverity {
        const val CRITICAL = "critical"
        const val HIGH = "high"
        const val MEDIUM = "medium"
    }

    // ==================== UI SETTINGS ====================

    /**
     * Minimum button size in dp (for elderly accessibility)
     */
    const val MIN_BUTTON_SIZE_DP = 80

    /**
     * Large text size in sp
     */
    const val LARGE_TEXT_SIZE_SP = 24

    /**
     * Extra large text size in sp
     */
    const val EXTRA_LARGE_TEXT_SIZE_SP = 32

    /**
     * Animation duration in milliseconds
     */
    const val ANIMATION_DURATION_MS = 300L

    /**
     * Listening animation pulse duration
     */
    const val LISTENING_PULSE_DURATION_MS = 1000L

    // ==================== MEDICATION SETTINGS ====================

    /**
     * Medication reminder advance time (10 minutes before)
     */
    const val MEDICATION_REMINDER_ADVANCE_MINUTES = 10

    /**
     * Medication reminder snooze time (5 minutes)
     */
    const val MEDICATION_SNOOZE_MINUTES = 5

    // ==================== NETWORK SETTINGS ====================

    /**
     * API timeout in seconds
     */
    const val API_TIMEOUT_SECONDS = 30L

    /**
     * Retry attempts for failed API calls
     */
    const val API_RETRY_ATTEMPTS = 3

    /**
     * Retry delay in milliseconds
     */
    const val API_RETRY_DELAY_MS = 1000L

    // ==================== PERMISSIONS ====================

    /**
     * Required permissions for the app
     */
    val REQUIRED_PERMISSIONS = arrayOf(
        android.Manifest.permission.RECORD_AUDIO,
        android.Manifest.permission.POST_NOTIFICATIONS
    )

    // ==================== SHARED PREFERENCES ====================

    /**
     * SharedPreferences file name
     */
    const val PREFS_NAME = "genvoice_prefs"

    /**
     * Preference keys
     */
    object PrefsKeys {
        const val SENIOR_ID = "senior_id"
        const val SENIOR_NAME = "senior_name"
        const val LAST_CHECKIN = "last_checkin"
        const val ONBOARDING_COMPLETE = "onboarding_complete"
        const val EMERGENCY_SERVICE_ENABLED = "emergency_service_enabled"
    }

    // ==================== NOTIFICATION CHANNELS ====================

    /**
     * Notification channel IDs
     */
    object NotificationChannels {
        const val MEDICATION_CHANNEL_ID = "medication_reminders"
        const val CHECKIN_CHANNEL_ID = "checkin_reminders"
        const val EMERGENCY_CHANNEL_ID = "emergency_service"
        const val EMERGENCY_ALERTS_CHANNEL_ID = "emergency_alerts"
        const val EMERGENCY_SERVICE_CHANNEL_ID = "emergency_monitoring_service"
    }

    /**
     * Notification IDs
     */
    object NotificationIds {
        const val MEDICATION_REMINDER = 1001
        const val CHECKIN_REMINDER = 1002
        const val EMERGENCY_SERVICE = 1003
    }
}
