package com.genvoice.caregiver.data.models

import com.google.gson.annotations.SerializedName

/**
 * Medication data model
 */
data class Medication(
    @SerializedName("id")
    val id: String,

    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("medication_name")
    val medicationName: String,

    @SerializedName("dosage")
    val dosage: String? = null,

    @SerializedName("frequency")
    val frequency: String? = null, // "daily", "twice_daily", "weekly", etc.

    @SerializedName("scheduled_times")
    val scheduledTimes: String? = null, // JSON array of times, e.g., "[\"08:00\", \"20:00\"]"

    @SerializedName("is_critical")
    val isCritical: Boolean = false,

    @SerializedName("instructions")
    val instructions: String? = null,

    @SerializedName("is_active")
    val isActive: Boolean = true,

    @SerializedName("created_at")
    val createdAt: String? = null
) {
    /**
     * Parse scheduled times from JSON string
     */
    fun getScheduledTimesList(): List<String> {
        return try {
            scheduledTimes
                ?.removeSurrounding("[", "]")
                ?.split(",")
                ?.map { it.trim().removeSurrounding("\"") }
                ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }
}

/**
 * Medication log (taken/missed record)
 */
data class MedicationLog(
    @SerializedName("id")
    val id: String,

    @SerializedName("medication_id")
    val medicationId: String,

    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("scheduled_time")
    val scheduledTime: String,

    @SerializedName("taken_at")
    val takenAt: String? = null,

    @SerializedName("status")
    val status: String, // "taken", "missed", "pending"

    @SerializedName("notes")
    val notes: String? = null,

    @SerializedName("created_at")
    val createdAt: String? = null
)

/**
 * Request to create a new medication
 */
data class MedicationCreateRequest(
    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("medication_name")
    val medicationName: String,

    @SerializedName("dosage")
    val dosage: String? = null,

    @SerializedName("frequency")
    val frequency: String,

    @SerializedName("scheduled_times")
    val scheduledTimes: List<String>,

    @SerializedName("is_critical")
    val isCritical: Boolean = false,

    @SerializedName("instructions")
    val instructions: String? = null
)

/**
 * Request to log medication taken
 */
data class MedicationTakenRequest(
    @SerializedName("medication_id")
    val medicationId: String,

    @SerializedName("senior_id")
    val seniorId: String,

    @SerializedName("taken_at")
    val takenAt: String? = null,

    @SerializedName("notes")
    val notes: String? = null
)

/**
 * Response after logging medication
 */
data class MedicationTakenResponse(
    @SerializedName("log_id")
    val logId: String,

    @SerializedName("medication_name")
    val medicationName: String,

    @SerializedName("taken_at")
    val takenAt: String,

    @SerializedName("status")
    val status: String
)

/**
 * Medication compliance summary
 */
data class MedicationCompliance(
    @SerializedName("medication_id")
    val medicationId: String,

    @SerializedName("medication_name")
    val medicationName: String,

    @SerializedName("total_scheduled")
    val totalScheduled: Int,

    @SerializedName("taken")
    val taken: Int,

    @SerializedName("missed")
    val missed: Int,

    @SerializedName("compliance_rate")
    val complianceRate: Float,

    @SerializedName("logs")
    val logs: List<MedicationLog>? = null
)
