package com.genvoice.caregiver.data.repository

import com.genvoice.caregiver.data.api.ApiClient
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.api.safeApiCall
import com.genvoice.caregiver.data.models.*
import com.genvoice.caregiver.utils.Constants
import com.genvoice.caregiver.utils.DateTimeUtils

/**
 * Repository for emergency operations
 */
class EmergencyRepository {

    private val api = ApiClient.api

    /**
     * Trigger emergency alert
     */
    suspend fun triggerEmergency(
        seniorId: String,
        alertType: String,
        severity: String,
        description: String? = null,
        location: String? = null
    ): Result<EmergencyAlertResponse> {
        val request = EmergencyAlertRequest(
            seniorId = seniorId,
            alertType = alertType,
            severity = severity,
            description = description,
            location = location,
            triggeredAt = DateTimeUtils.getCurrentIso8601Timestamp()
        )
        return safeApiCall { api.triggerEmergency(request) }
    }

    /**
     * Trigger manual emergency (SOS button pressed)
     */
    suspend fun triggerManualEmergency(
        seniorId: String,
        description: String? = "Emergency button pressed"
    ): Result<EmergencyAlertResponse> {
        return triggerEmergency(
            seniorId = seniorId,
            alertType = EmergencyType.MANUAL,
            severity = Constants.EmergencySeverity.CRITICAL,
            description = description
        )
    }

    /**
     * Trigger keyword-detected emergency
     */
    suspend fun triggerKeywordEmergency(
        seniorId: String,
        severity: String,
        description: String,
        detectedText: String
    ): Result<EmergencyAlertResponse> {
        return triggerEmergency(
            seniorId = seniorId,
            alertType = EmergencyType.KEYWORD,
            severity = severity,
            description = "$description - Detected: \"$detectedText\""
        )
    }

    /**
     * Trigger missed check-in emergency
     */
    suspend fun triggerMissedCheckInEmergency(
        seniorId: String,
        checkInType: String
    ): Result<EmergencyAlertResponse> {
        return triggerEmergency(
            seniorId = seniorId,
            alertType = EmergencyType.MISSED_CHECKIN,
            severity = Constants.EmergencySeverity.MEDIUM,
            description = "Missed $checkInType check-in"
        )
    }

    /**
     * Get emergency history for a senior
     */
    suspend fun getEmergencyHistory(
        seniorId: String,
        limit: Int? = 10
    ): Result<List<Emergency>> {
        return safeApiCall { api.getEmergencies(seniorId, limit) }
    }

    /**
     * Get active emergencies count
     */
    suspend fun getActiveEmergenciesCount(seniorId: String): Int {
        return when (val result = getEmergencyHistory(seniorId)) {
            is Result.Success -> result.data.count { it.status == "active" }
            else -> 0
        }
    }
}
