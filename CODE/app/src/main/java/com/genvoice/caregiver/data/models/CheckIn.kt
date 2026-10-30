package com.genvoice.caregiver.data.models

import com.google.gson.annotations.SerializedName

/**
 * Check-in data model
 */
data class CheckIn(
    @SerializedName("id")
    val id: String,

    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("check_in_type")
    val checkInType: String, // "morning", "evening", "manual"

    @SerializedName("scheduled_time")
    val scheduledTime: String? = null,

    @SerializedName("completed_at")
    val completedAt: String? = null,

    @SerializedName("conversation_transcript")
    val conversationTranscript: String? = null,

    @SerializedName("wellness_status")
    val wellnessStatus: String? = null, // "good", "fair", "poor"

    @SerializedName("wellness_score")
    val wellnessScore: Int? = null,

    @SerializedName("concerns_detected")
    val concernsDetected: String? = null,

    @SerializedName("concern_severity")
    val concernSeverity: Int? = null,

    @SerializedName("ai_summary")
    val aiSummary: String? = null,

    @SerializedName("status")
    val status: String = "pending", // "pending", "completed", "missed"

    @SerializedName("created_at")
    val createdAt: String? = null
)

/**
 * Request to start a check-in
 */
data class CheckInStartRequest(
    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("check_in_type")
    val checkInType: String,

    @SerializedName("scheduled_time")
    val scheduledTime: String? = null
)

/**
 * Response when starting a check-in
 */
data class CheckInStartResponse(
    @SerializedName("check_in_id")
    val checkInId: String,

    @SerializedName("greeting")
    val greeting: String? = null,

    @SerializedName("status")
    val status: String
)

/**
 * Request to submit a completed check-in
 */
data class CheckInSubmitRequest(
    @SerializedName("check_in_id")
    val checkInId: String,

    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("conversation_transcript")
    val conversationTranscript: String,

    @SerializedName("completed_at")
    val completedAt: String,

    @SerializedName("wellness_status")
    val wellnessStatus: String? = null,

    @SerializedName("wellness_score")
    val wellnessScore: Int? = null,

    @SerializedName("concerns_detected")
    val concernsDetected: String? = null,

    @SerializedName("concern_severity")
    val concernSeverity: Int? = null
)

/**
 * Response after submitting a check-in
 */
data class CheckInSubmitResponse(
    @SerializedName("check_in_id")
    val checkInId: String,

    @SerializedName("wellness_status")
    val wellnessStatus: String,

    @SerializedName("wellness_score")
    val wellnessScore: Int,

    @SerializedName("concerns_detected")
    val concernsDetected: List<String>? = null,

    @SerializedName("concern_severity")
    val concernSeverity: Int? = null,

    @SerializedName("ai_summary")
    val aiSummary: String? = null,

    @SerializedName("family_notified")
    val familyNotified: Boolean = false,

    @SerializedName("sms_sent")
    val smsSent: Boolean = false
)

/**
 * Conversation history message
 */
data class ConversationMessage(
    @SerializedName("role")
    val role: String, // "user" or "assistant"

    @SerializedName("content")
    val content: String
)

/**
 * Request for AI conversation turn
 */
data class AiConversationRequest(
    @SerializedName("user_message")
    val userMessage: String? = null,

    @SerializedName("conversation_history")
    val conversationHistory: List<ConversationMessage> = emptyList(),

    @SerializedName("is_first_message")
    val isFirstMessage: Boolean = false,

    @SerializedName("senior_name")
    val seniorName: String = "Margaret"
)

/**
 * Response from AI conversation
 */
data class AiConversationResponse(
    @SerializedName("ai_response")
    val aiResponse: String,

    @SerializedName("conversation_complete")
    val conversationComplete: Boolean = false,

    @SerializedName("offering_schedule")
    val offeringSchedule: Boolean = false
)

/**
 * Request to schedule a check-in
 */
data class ScheduleCheckInRequest(
    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("minutes_from_now")
    val minutesFromNow: Int
)

/**
 * Response from scheduling a check-in
 */
data class ScheduleCheckInResponse(
    @SerializedName("schedule_id")
    val scheduleId: String,

    @SerializedName("scheduled_time")
    val scheduledTime: String,

    @SerializedName("minutes_from_now")
    val minutesFromNow: Int,

    @SerializedName("message")
    val message: String
)
