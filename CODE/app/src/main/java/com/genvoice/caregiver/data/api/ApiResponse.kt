package com.genvoice.caregiver.data.api

import com.google.gson.annotations.SerializedName

/**
 * Generic API response wrapper
 */
data class ApiResponse<T>(
    @SerializedName("success")
    val success: Boolean,

    @SerializedName("data")
    val data: T? = null,

    @SerializedName("error")
    val error: String? = null,

    @SerializedName("message")
    val message: String? = null,

    @SerializedName("count")
    val count: Int? = null
)

/**
 * Result wrapper for handling API responses
 */
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val exception: Exception? = null) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

/**
 * Extension function to convert ApiResponse to Result
 */
fun <T> ApiResponse<T>.toResult(): Result<T> {
    return if (success && data != null) {
        Result.Success(data)
    } else {
        Result.Error(error ?: message ?: "Unknown error occurred")
    }
}

/**
 * Health check response
 */
data class HealthResponse(
    @SerializedName("status")
    val status: String,

    @SerializedName("service")
    val service: String? = null,

    @SerializedName("database")
    val database: String? = null,

    @SerializedName("stats")
    val stats: HealthStats? = null
)

data class HealthStats(
    @SerializedName("active_seniors")
    val activeSeniors: Int,

    @SerializedName("completed_checkins")
    val completedCheckins: Int
)
