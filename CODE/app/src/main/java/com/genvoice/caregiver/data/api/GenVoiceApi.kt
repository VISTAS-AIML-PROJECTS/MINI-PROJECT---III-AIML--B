package com.genvoice.caregiver.data.api

import com.genvoice.caregiver.data.models.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Retrofit API interface for GenVoice backend
 */
interface GenVoiceApi {

    // ==================== SYSTEM ENDPOINTS ====================

    /**
     * Health check
     */
    @GET("health")
    suspend fun health(): Response<HealthResponse>

    // ==================== SENIOR ENDPOINTS ====================

    /**
     * Get all seniors
     */
    @GET("api/v1/seniors")
    suspend fun getSeniors(): Response<ApiResponse<List<Senior>>>

    /**
     * Get senior details by ID
     */
    @GET("api/v1/seniors/{id}")
    suspend fun getSenior(
        @Path("id") seniorId: String
    ): Response<ApiResponse<Senior>>

    /**
     * Get senior dashboard (complete overview)
     */
    @GET("api/v1/seniors/{id}/dashboard")
    suspend fun getDashboard(
        @Path("id") seniorId: String
    ): Response<ApiResponse<Dashboard>>

    // ==================== CHECK-IN ENDPOINTS ====================

    /**
     * Start a new check-in
     */
    @POST("api/v1/checkin/start")
    suspend fun startCheckIn(
        @Body request: CheckInStartRequest
    ): Response<ApiResponse<CheckInStartResponse>>

    /**
     * Submit completed check-in
     */
    @POST("api/v1/checkin/submit")
    suspend fun submitCheckIn(
        @Body request: CheckInSubmitRequest
    ): Response<ApiResponse<CheckInSubmitResponse>>

    /**
     * Get check-in history for a senior
     */
    @GET("api/v1/seniors/{id}/checkins")
    suspend fun getCheckIns(
        @Path("id") seniorId: String,
        @Query("limit") limit: Int? = null
    ): Response<ApiResponse<List<CheckIn>>>

    /**
     * AI Conversation - Get intelligent response
     */
    @POST("api/v1/checkin/conversation")
    suspend fun aiConversation(
        @Body request: AiConversationRequest
    ): Response<ApiResponse<AiConversationResponse>>

    /**
     * Schedule a check-in for later
     */
    @POST("api/v1/checkin/schedule")
    suspend fun scheduleCheckIn(
        @Body request: ScheduleCheckInRequest
    ): Response<ApiResponse<ScheduleCheckInResponse>>

    // ==================== MEDICATION ENDPOINTS ====================

    /**
     * Create new medication schedule
     */
    @POST("api/v1/medications")
    suspend fun createMedication(
        @Body request: MedicationCreateRequest
    ): Response<ApiResponse<Medication>>

    /**
     * Get medications for a senior
     */
    @GET("api/v1/seniors/{id}/medications")
    suspend fun getMedications(
        @Path("id") seniorId: String
    ): Response<ApiResponse<List<Medication>>>

    /**
     * Log medication taken
     */
    @POST("api/v1/medications/taken")
    suspend fun logMedicationTaken(
        @Body request: MedicationTakenRequest
    ): Response<ApiResponse<MedicationTakenResponse>>

    /**
     * Get medication logs (compliance history)
     */
    @GET("api/v1/medications/{id}/logs")
    suspend fun getMedicationLogs(
        @Path("id") medicationId: String,
        @Query("days") days: Int? = 7
    ): Response<ApiResponse<MedicationCompliance>>

    // ==================== EMERGENCY ENDPOINTS ====================

    /**
     * Trigger emergency alert
     */
    @POST("api/v1/emergency/alert")
    suspend fun triggerEmergency(
        @Body request: EmergencyAlertRequest
    ): Response<ApiResponse<EmergencyAlertResponse>>

    /**
     * Get emergency history for a senior
     */
    @GET("api/v1/seniors/{id}/emergencies")
    suspend fun getEmergencies(
        @Path("id") seniorId: String,
        @Query("limit") limit: Int? = null
    ): Response<ApiResponse<List<Emergency>>>

    // ==================== BLUEPRINT CONVERSATION ENDPOINTS ====================

    /**
     * Get conversation details (Blueprint Architecture)
     */
    @GET("api/v1/conversations/{conversation_id}")
    suspend fun getConversation(
        @Path("conversation_id") conversationId: String
    ): Response<ApiResponse<ConversationDetails>>

    /**
     * Get senior's conversation history (Blueprint Architecture)
     */
    @GET("api/v1/seniors/{senior_id}/conversations")
    suspend fun getSeniorConversations(
        @Path("senior_id") seniorId: String
    ): Response<ApiResponse<SeniorConversationsResponse>>

    /**
     * Get latest summary for senior (Blueprint Architecture)
     */
    @GET("api/v1/seniors/{senior_id}/summary/latest")
    suspend fun getLatestSummary(
        @Path("senior_id") seniorId: String
    ): Response<ApiResponse<ConversationSummary>>
}
