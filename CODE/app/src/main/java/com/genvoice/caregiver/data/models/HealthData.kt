package com.genvoice.caregiver.data.models

/**
 * Health Data Collection Framework
 * Tracks ACTUAL data collected during conversation
 */
data class HealthDataCollection(
    // Required data points - must collect ALL before ending conversation
    var sleepQuality: SleepQuality? = null,          // How did they sleep?
    var physicalFeeling: PhysicalFeeling? = null,    // How are they feeling physically?
    var painStatus: PainStatus? = null,              // Any pain?
    var moodStatus: MoodStatus? = null,              // How is their mood?
    var medicationTaken: MedicationStatus? = null,   // Did they take medicine?
    var foodIntake: FoodIntake? = null               // Did they eat well?
) {
    /**
     * Check if ALL required data has been collected
     */
    fun isComplete(): Boolean {
        return sleepQuality != null &&
               physicalFeeling != null &&
               painStatus != null &&
               moodStatus != null &&
               medicationTaken != null &&
               foodIntake != null
    }

    /**
     * Get list of missing data points
     */
    fun getMissingData(): List<String> {
        val missing = mutableListOf<String>()
        if (sleepQuality == null) missing.add("sleep quality")
        if (physicalFeeling == null) missing.add("physical feeling")
        if (painStatus == null) missing.add("pain status")
        if (moodStatus == null) missing.add("mood")
        if (medicationTaken == null) missing.add("medication")
        if (foodIntake == null) missing.add("food intake")
        return missing
    }

    /**
     * Calculate wellness score based on ACTUAL collected data
     * Score range: 0-100
     */
    fun calculateWellnessScore(): Int {
        if (!isComplete()) {
            throw IllegalStateException("Cannot calculate score - data incomplete")
        }

        var totalScore = 0
        var maxScore = 0

        // Sleep Quality (0-20 points)
        maxScore += 20
        totalScore += when (sleepQuality) {
            SleepQuality.EXCELLENT -> 20
            SleepQuality.GOOD -> 15
            SleepQuality.FAIR -> 10
            SleepQuality.POOR -> 5
            SleepQuality.VERY_POOR -> 0
            else -> 0
        }

        // Physical Feeling (0-20 points)
        maxScore += 20
        totalScore += when (physicalFeeling) {
            PhysicalFeeling.EXCELLENT -> 20
            PhysicalFeeling.GOOD -> 15
            PhysicalFeeling.FAIR -> 10
            PhysicalFeeling.POOR -> 5
            PhysicalFeeling.VERY_POOR -> 0
            else -> 0
        }

        // Pain Status (0-15 points) - CRITICAL
        maxScore += 15
        totalScore += when (painStatus?.severity) {
            null, 0 -> 15  // No pain
            in 1..3 -> 12  // Mild pain
            in 4..6 -> 8   // Moderate pain
            in 7..8 -> 4   // Severe pain
            in 9..10 -> 0  // Critical pain
            else -> 0
        }

        // Mood Status (0-15 points)
        maxScore += 15
        totalScore += when (moodStatus) {
            MoodStatus.HAPPY -> 15
            MoodStatus.CONTENT -> 12
            MoodStatus.NEUTRAL -> 8
            MoodStatus.SAD -> 4
            MoodStatus.DEPRESSED -> 0
            else -> 0
        }

        // Medication Taken (0-15 points) - CRITICAL
        maxScore += 15
        totalScore += when (medicationTaken) {
            MedicationStatus.TAKEN_ON_TIME -> 15
            MedicationStatus.TAKEN_LATE -> 10
            MedicationStatus.FORGOT -> 0
            MedicationStatus.NOT_APPLICABLE -> 15
            else -> 0
        }

        // Food Intake (0-15 points)
        maxScore += 15
        totalScore += when (foodIntake) {
            FoodIntake.GOOD -> 15
            FoodIntake.FAIR -> 10
            FoodIntake.POOR -> 5
            FoodIntake.NONE -> 0
            else -> 0
        }

        // Calculate final score (0-100)
        return (totalScore * 100) / maxScore
    }

    /**
     * Get wellness status based on score
     */
    fun getWellnessStatus(): String {
        val score = calculateWellnessScore()
        return when {
            score >= 85 -> "excellent"
            score >= 70 -> "good"
            score >= 50 -> "fair"
            else -> "poor"
        }
    }

    /**
     * Get list of concerns detected
     */
    fun getConcerns(): List<String> {
        val concerns = mutableListOf<String>()

        // Pain concern
        painStatus?.let {
            if (it.severity > 0) {
                concerns.add("Pain reported: ${it.location} (${it.severity}/10)")
            }
        }

        // Medication concern
        if (medicationTaken == MedicationStatus.FORGOT) {
            concerns.add("Forgot to take medication")
        }

        // Sleep concern
        if (sleepQuality == SleepQuality.POOR || sleepQuality == SleepQuality.VERY_POOR) {
            concerns.add("Poor sleep quality")
        }

        // Mood concern
        if (moodStatus == MoodStatus.SAD || moodStatus == MoodStatus.DEPRESSED) {
            concerns.add("Low mood detected")
        }

        // Food concern
        if (foodIntake == FoodIntake.POOR || foodIntake == FoodIntake.NONE) {
            concerns.add("Poor food intake")
        }

        return concerns
    }
}

// Data models for each health aspect

enum class SleepQuality {
    EXCELLENT,  // Slept great
    GOOD,       // Slept well
    FAIR,       // Okay sleep
    POOR,       // Slept badly
    VERY_POOR   // Barely slept
}

enum class PhysicalFeeling {
    EXCELLENT,  // Feeling great
    GOOD,       // Feeling good
    FAIR,       // Okay
    POOR,       // Not feeling well
    VERY_POOR   // Feeling very sick
}

data class PainStatus(
    val hasPain: Boolean,
    val location: String? = null,  // e.g., "back", "knee", "chest"
    val severity: Int = 0          // 0-10 scale
)

enum class MoodStatus {
    HAPPY,      // Happy/joyful
    CONTENT,    // Content/peaceful
    NEUTRAL,    // Neutral
    SAD,        // Sad/down
    DEPRESSED   // Very depressed
}

enum class MedicationStatus {
    TAKEN_ON_TIME,    // Took medication on time
    TAKEN_LATE,       // Took medication but late
    FORGOT,           // Forgot to take medication
    NOT_APPLICABLE    // No medication scheduled
}

enum class FoodIntake {
    GOOD,   // Ate well
    FAIR,   // Ate something
    POOR,   // Barely ate
    NONE    // Didn't eat
}
