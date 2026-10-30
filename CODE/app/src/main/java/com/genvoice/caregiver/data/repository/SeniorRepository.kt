package com.genvoice.caregiver.data.repository

import com.genvoice.caregiver.data.api.ApiClient
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.api.safeApiCall
import com.genvoice.caregiver.data.models.Dashboard
import com.genvoice.caregiver.data.models.Senior

/**
 * Repository for senior-related operations
 */
class SeniorRepository {

    private val api = ApiClient.api

    /**
     * Get all seniors
     */
    suspend fun getAllSeniors(): Result<List<Senior>> {
        return safeApiCall { api.getSeniors() }
    }

    /**
     * Get senior details by ID
     */
    suspend fun getSenior(seniorId: String): Result<Senior> {
        return safeApiCall { api.getSenior(seniorId) }
    }

    /**
     * Get senior dashboard (complete overview)
     */
    suspend fun getDashboard(seniorId: String): Result<Dashboard> {
        return safeApiCall { api.getDashboard(seniorId) }
    }

    /**
     * Check if backend is reachable
     */
    suspend fun checkBackendHealth(): Boolean {
        return ApiClient.isBackendReachable()
    }
}
