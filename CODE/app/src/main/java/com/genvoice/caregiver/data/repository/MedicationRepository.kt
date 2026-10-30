package com.genvoice.caregiver.data.repository

import com.genvoice.caregiver.data.api.ApiClient
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.api.safeApiCall
import com.genvoice.caregiver.data.models.*
import com.genvoice.caregiver.utils.DateTimeUtils

/**
 * Repository for medication operations
 */
class MedicationRepository {

    private val api = ApiClient.api

    /**
     * Create a new medication schedule
     */
    suspend fun createMedication(
        seniorId: String,
        medicationName: String,
        dosage: String,
        frequency: String,
        scheduledTimes: List<String>,
        isCritical: Boolean = false,
        instructions: String? = null
    ): Result<Medication> {
        val request = MedicationCreateRequest(
            seniorId = seniorId,
            medicationName = medicationName,
            dosage = dosage,
            frequency = frequency,
            scheduledTimes = scheduledTimes,
            isCritical = isCritical,
            instructions = instructions
        )
        return safeApiCall { api.createMedication(request) }
    }

    /**
     * Get medications for a senior
     */
    suspend fun getMedications(seniorId: String): Result<List<Medication>> {
        return safeApiCall { api.getMedications(seniorId) }
    }

    /**
     * Log medication taken
     */
    suspend fun logMedicationTaken(
        medicationId: String,
        seniorId: String,
        notes: String? = null
    ): Result<MedicationTakenResponse> {
        val request = MedicationTakenRequest(
            medicationId = medicationId,
            seniorId = seniorId,
            takenAt = DateTimeUtils.getCurrentIso8601Timestamp(),
            notes = notes
        )
        return safeApiCall { api.logMedicationTaken(request) }
    }

    /**
     * Get medication compliance logs
     */
    suspend fun getMedicationCompliance(
        medicationId: String,
        days: Int = 7
    ): Result<MedicationCompliance> {
        return safeApiCall { api.getMedicationLogs(medicationId, days) }
    }

    /**
     * Check if medication is due now
     */
    fun isMedicationDue(medication: Medication): Boolean {
        val currentHour = DateTimeUtils.getCurrentHour()
        val currentMinute = java.util.Calendar.getInstance().get(java.util.Calendar.MINUTE)
        val currentTime = String.format("%02d:%02d", currentHour, currentMinute)

        return medication.getScheduledTimesList().any { scheduledTime ->
            // Check if current time matches scheduled time (within 10 minutes)
            val scheduled = scheduledTime.split(":")
            if (scheduled.size >= 2) {
                val scheduledHour = scheduled[0].toIntOrNull() ?: return@any false
                val scheduledMinute = scheduled[1].toIntOrNull() ?: return@any false

                val timeDiff = (currentHour * 60 + currentMinute) - (scheduledHour * 60 + scheduledMinute)
                timeDiff in 0..10 // Due if within 10 minutes
            } else {
                false
            }
        }
    }

    /**
     * Get next medication time
     */
    fun getNextMedicationTime(medication: Medication): String? {
        val times = medication.getScheduledTimesList()
        if (times.isEmpty()) return null

        val currentHour = DateTimeUtils.getCurrentHour()
        val currentMinute = java.util.Calendar.getInstance().get(java.util.Calendar.MINUTE)
        val currentTimeMinutes = currentHour * 60 + currentMinute

        // Find next scheduled time today
        val nextTime = times
            .mapNotNull { time ->
                val parts = time.split(":")
                if (parts.size >= 2) {
                    val hour = parts[0].toIntOrNull()
                    val minute = parts[1].toIntOrNull()
                    if (hour != null && minute != null) {
                        val scheduleMinutes = hour * 60 + minute
                        if (scheduleMinutes > currentTimeMinutes) {
                            time
                        } else null
                    } else null
                } else null
            }
            .minOrNull()

        return nextTime ?: times.firstOrNull() // If no time left today, return first time (tomorrow)
    }
}
