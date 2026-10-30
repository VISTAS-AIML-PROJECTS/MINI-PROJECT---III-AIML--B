package com.genvoice.caregiver.data.models

import com.google.gson.annotations.SerializedName

/**
 * Emergency alert data model
 */
data class Emergency(
    @SerializedName("id")
    val id: String,

    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("alert_type")
    val alertType: String, // "manual", "keyword", "missed_checkin", "fall_detection"

    @SerializedName("severity")
    val severity: String, // "critical", "high", "medium"

    @SerializedName("description")
    val description: String? = null,

    @SerializedName("location")
    val location: String? = null,

    @SerializedName("triggered_at")
    val triggeredAt: String,

    @SerializedName("resolved_at")
    val resolvedAt: String? = null,

    @SerializedName("status")
    val status: String = "active", // "active", "resolved", "false_alarm"

    @SerializedName("family_notified")
    val familyNotified: Boolean = false,

    @SerializedName("sms_sent")
    val smsSent: Boolean = false,

    @SerializedName("created_at")
    val createdAt: String? = null
)

/**
 * Request to trigger emergency alert
 */
data class EmergencyAlertRequest(
    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("alert_type")
    val alertType: String, // "manual", "keyword", "missed_checkin", "fall_detection"

    @SerializedName("severity")
    val severity: String, // "critical", "high", "medium"

    @SerializedName("description")
    val description: String? = null,

    @SerializedName("location")
    val location: String? = null,

    @SerializedName("triggered_at")
    val triggeredAt: String? = null
)

/**
 * Response after triggering emergency
 */
data class EmergencyAlertResponse(
    @SerializedName("alert_id")
    val alertId: String,

    @SerializedName("status")
    val status: String,

    @SerializedName("family_notified")
    val familyNotified: Boolean,

    @SerializedName("sms_sent")
    val smsSent: Boolean,

    @SerializedName("message")
    val message: String? = null
)

/**
 * Emergency types
 */
object EmergencyType {
    const val MANUAL = "manual"              // User pressed emergency button
    const val KEYWORD = "keyword"            // Emergency keyword detected
    const val MISSED_CHECKIN = "missed_checkin"  // Missed scheduled check-in
    const val FALL_DETECTION = "fall_detection"  // Fall detected (future feature)
}
