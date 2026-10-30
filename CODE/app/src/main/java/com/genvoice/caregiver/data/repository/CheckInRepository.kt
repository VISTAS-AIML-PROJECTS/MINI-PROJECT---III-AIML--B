package com.genvoice.caregiver.data.repository

import com.genvoice.caregiver.data.api.ApiClient
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.api.safeApiCall
import com.genvoice.caregiver.data.models.*
import com.genvoice.caregiver.utils.Constants
import com.genvoice.caregiver.utils.DateTimeUtils

/**
 * Repository for check-in operations
 */
class CheckInRepository {

    private val api = ApiClient.api

    /**
     * Start a new check-in
     */
    suspend fun startCheckIn(
        seniorId: String,
        checkInType: String
    ): Result<CheckInStartResponse> {
        val request = CheckInStartRequest(
            seniorId = seniorId,
            checkInType = checkInType,
            scheduledTime = DateTimeUtils.getCurrentIso8601Timestamp()
        )
        return safeApiCall { api.startCheckIn(request) }
    }

    /**
     * Submit completed check-in with conversation
     */
    suspend fun submitCheckIn(
        checkInId: String,
        seniorId: String,
        conversationTranscript: String,
        wellnessStatus: String,
        wellnessScore: Int,
        concernsDetected: String? = null,
        concernSeverity: Int? = null
    ): Result<CheckInSubmitResponse> {
        val request = CheckInSubmitRequest(
            checkInId = checkInId,
            seniorId = seniorId,
            conversationTranscript = conversationTranscript,
            completedAt = DateTimeUtils.getCurrentIso8601Timestamp(),
            wellnessStatus = wellnessStatus,
            wellnessScore = wellnessScore,
            concernsDetected = concernsDetected,
            concernSeverity = concernSeverity
        )
        return safeApiCall { api.submitCheckIn(request) }
    }

    /**
     * Get check-in history for a senior
     */
    suspend fun getCheckInHistory(
        seniorId: String,
        limit: Int? = 10
    ): Result<List<CheckIn>> {
        return safeApiCall { api.getCheckIns(seniorId, limit) }
    }

    /**
     * Start morning check-in
     */
    suspend fun startMorningCheckIn(seniorId: String): Result<CheckInStartResponse> {
        return startCheckIn(seniorId, Constants.CheckInType.MORNING)
    }

    /**
     * Start evening check-in
     */
    suspend fun startEveningCheckIn(seniorId: String): Result<CheckInStartResponse> {
        return startCheckIn(seniorId, Constants.CheckInType.EVENING)
    }

    /**
     * Start manual check-in (any time)
     */
    suspend fun startManualCheckIn(seniorId: String): Result<CheckInStartResponse> {
        return startCheckIn(seniorId, Constants.CheckInType.MANUAL)
    }

    /**
     * Get AI conversation response
     */
    suspend fun getAiConversationResponse(
        userMessage: String?,
        conversationHistory: List<ConversationMessage>,
        isFirstMessage: Boolean,
        seniorName: String
    ): Result<AiConversationResponse> {
        val request = AiConversationRequest(
            userMessage = userMessage,
            conversationHistory = conversationHistory,
            isFirstMessage = isFirstMessage,
            seniorName = seniorName
        )
        return safeApiCall { api.aiConversation(request) }
    }

    /**
     * Schedule a check-in for later
     */
    suspend fun scheduleCheckIn(
        seniorId: String,
        minutesFromNow: Int
    ): Result<ScheduleCheckInResponse> {
        val request = ScheduleCheckInRequest(
            seniorId = seniorId,
            minutesFromNow = minutesFromNow
        )
        return safeApiCall { api.scheduleCheckIn(request) }
    }
}
