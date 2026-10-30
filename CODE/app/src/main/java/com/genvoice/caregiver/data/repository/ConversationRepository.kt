package com.genvoice.caregiver.data.repository

import com.genvoice.caregiver.data.api.ApiClient
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.api.safeApiCall
import com.genvoice.caregiver.data.models.*

/**
 * Repository for Blueprint Conversation operations (Caregiver view)
 */
class ConversationRepository {

    private val api = ApiClient.api

    /**
     * Get conversation details with full transcript
     */
    suspend fun getConversation(
        conversationId: String
    ): Result<ConversationDetails> {
        return safeApiCall { api.getConversation(conversationId) }
    }

    /**
     * Get conversation history for a senior
     */
    suspend fun getSeniorConversations(
        seniorId: String
    ): Result<SeniorConversationsResponse> {
        return safeApiCall { api.getSeniorConversations(seniorId) }
    }

    /**
     * Get latest summary for a senior
     */
    suspend fun getLatestSummary(
        seniorId: String
    ): Result<ConversationSummary> {
        return safeApiCall { api.getLatestSummary(seniorId) }
    }
}
