package com.genvoice.caregiver.data.models

import com.google.gson.annotations.SerializedName

/**
 * Conversation models for Blueprint Architecture (Caregiver view)
 */

/**
 * Conversation record
 */
data class Conversation(
    @SerializedName("id")
    val id: String,

    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("current_state")
    val currentState: String,

    @SerializedName("current_topic")
    val currentTopic: String? = null,

    @SerializedName("status")
    val status: String, // "active", "completed", "urgent"

    @SerializedName("started_at")
    val startedAt: String,

    @SerializedName("completed_at")
    val completedAt: String? = null
)

/**
 * Message item in conversation
 */
data class ConversationMessageItem(
    @SerializedName("id")
    val id: String,

    @SerializedName("conversation_id")
    val conversationId: String,

    @SerializedName("message_id")
    val messageId: String,

    @SerializedName("speaker")
    val speaker: String, // "user" or "assistant"

    @SerializedName("content")
    val content: String,

    @SerializedName("intent")
    val intent: String? = null,

    @SerializedName("confidence")
    val confidence: Double? = null,

    @SerializedName("created_at")
    val createdAt: String
)

/**
 * Conversation details (with full transcript)
 */
data class ConversationDetails(
    @SerializedName("conversation")
    val conversation: Conversation,

    @SerializedName("message_count")
    val messageCount: Int,

    @SerializedName("messages")
    val messages: List<ConversationMessageItem>
)

/**
 * Summary for completed conversation
 */
data class ConversationSummary(
    @SerializedName("id")
    val id: String,

    @SerializedName("conversation_id")
    val conversationId: String,

    @SerializedName("summary_text")
    val summaryText: String? = null,

    @SerializedName("self_reported_mood")
    val selfReportedMood: String? = null,

    @SerializedName("sleep_response")
    val sleepResponse: String? = null,

    @SerializedName("meals_response")
    val mealsResponse: String? = null,

    @SerializedName("social_connection_response")
    val socialConnectionResponse: String? = null,

    @SerializedName("assistance_needed")
    val assistanceNeeded: Boolean = false,

    @SerializedName("assistance_details")
    val assistanceDetails: String? = null,

    @SerializedName("potential_urgent_concern")
    val potentialUrgentConcern: String? = null,

    @SerializedName("conversation_status")
    val conversationStatus: String? = null,

    @SerializedName("created_at")
    val createdAt: String
)

/**
 * Senior conversations list response
 */
data class SeniorConversationsResponse(
    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("conversations")
    val conversations: List<Conversation>
)

/**
 * Enhanced dashboard with Blueprint data
 */
data class BlueprintDashboard(
    @SerializedName("senior")
    val senior: DashboardSenior,

    @SerializedName("latest_conversation")
    val latestConversation: LatestConversationData,

    @SerializedName("emergencies")
    val emergencies: EmergencyData,

    @SerializedName("family_contacts")
    val familyContacts: List<FamilyContact>
)

/**
 * Senior info for dashboard
 */
data class DashboardSenior(
    @SerializedName("id")
    val id: String,

    @SerializedName("name")
    val name: String,

    @SerializedName("phone")
    val phone: String? = null,

    @SerializedName("last_check_in")
    val lastCheckIn: String? = null
)

/**
 * Latest conversation data
 */
data class LatestConversationData(
    @SerializedName("conversation")
    val conversation: Conversation? = null,

    @SerializedName("messages")
    val messages: List<ConversationMessageItem> = emptyList(),

    @SerializedName("message_count")
    val messageCount: Int = 0
)

/**
 * Emergency data
 */
data class EmergencyData(
    @SerializedName("active_count")
    val activeCount: Int,

    @SerializedName("recent")
    val recent: List<Emergency> = emptyList()
)

/**
 * Family contact
 */
data class FamilyContact(
    @SerializedName("name")
    val name: String,

    @SerializedName("relationship_type")
    val relationshipType: String,

    @SerializedName("phone_number")
    val phoneNumber: String
)
