package com.genvoice.caregiver.utils

/**
 * Detects emergency keywords in speech
 */
object KeywordDetector {

    /**
     * Check if text contains emergency keywords
     * Returns pair of (detected: Boolean, severity: String)
     */
    fun detectEmergency(text: String): Pair<Boolean, String> {
        val lowerText = text.lowercase()

        // Critical keywords (immediate emergency)
        val criticalKeywords = listOf(
            "911",
            "ambulance",
            "can't breathe",
            "chest pain",
            "heart attack",
            "stroke",
            "bleeding"
        )

        // High severity keywords
        val highSeverityKeywords = listOf(
            "fallen",
            "fell",
            "can't get up",
            "emergency",
            "help me"
        )

        // Medium severity keywords
        val mediumSeverityKeywords = listOf(
            "help",
            "hurt",
            "pain",
            "sick",
            "dizzy",
            "weak",
            "confused"
        )

        // Check for critical keywords first
        for (keyword in criticalKeywords) {
            if (lowerText.contains(keyword)) {
                return Pair(true, Constants.EmergencySeverity.CRITICAL)
            }
        }

        // Check for high severity keywords
        for (keyword in highSeverityKeywords) {
            if (lowerText.contains(keyword)) {
                return Pair(true, Constants.EmergencySeverity.HIGH)
            }
        }

        // Check for medium severity keywords
        for (keyword in mediumSeverityKeywords) {
            if (lowerText.contains(keyword)) {
                return Pair(true, Constants.EmergencySeverity.MEDIUM)
            }
        }

        return Pair(false, "")
    }

    /**
     * Extract emergency context from text
     * Returns a brief description of what was detected
     */
    fun extractEmergencyContext(text: String): String {
        val lowerText = text.lowercase()

        return when {
            lowerText.contains("fallen") || lowerText.contains("fell") -> "Fall detected"
            lowerText.contains("chest pain") -> "Chest pain reported"
            lowerText.contains("can't breathe") -> "Breathing difficulty"
            lowerText.contains("dizzy") -> "Dizziness reported"
            lowerText.contains("pain") -> "Pain reported"
            lowerText.contains("sick") -> "Illness reported"
            lowerText.contains("hurt") -> "Injury reported"
            lowerText.contains("help") -> "Help requested"
            else -> "Emergency situation"
        }
    }

    /**
     * Check if text is likely a false positive
     * (e.g., "I'm feeling good, no pain")
     */
    fun isFalsePositive(text: String): Boolean {
        val lowerText = text.lowercase()

        val negationPatterns = listOf(
            "no pain",
            "no help",
            "don't hurt",
            "doesn't hurt",
            "not hurt",
            "not sick",
            "feeling good",
            "feeling better",
            "I'm fine",
            "I'm okay",
            "I'm good"
        )

        return negationPatterns.any { lowerText.contains(it) }
    }

    /**
     * Get confirmation message based on severity
     */
    fun getConfirmationMessage(severity: String): String {
        return when (severity) {
            Constants.EmergencySeverity.CRITICAL ->
                "I detected an emergency! Calling for help immediately!"
            Constants.EmergencySeverity.HIGH ->
                "It sounds like you need help. Should I alert your family?"
            Constants.EmergencySeverity.MEDIUM ->
                "Are you okay? Do you need me to contact someone?"
            else -> "Is everything alright?"
        }
    }

    /**
     * Get TTS message for emergency alert sent
     */
    fun getAlertSentMessage(): String {
        return "Your family has been notified. Help is on the way. Stay calm, someone will be there soon."
    }
}
