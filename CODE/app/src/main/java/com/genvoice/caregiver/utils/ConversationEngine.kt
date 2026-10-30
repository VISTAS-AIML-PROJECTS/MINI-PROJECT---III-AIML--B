package com.genvoice.caregiver.utils

/**
 * Handles conversation flow for check-ins
 * Simple rule-based conversation (no AI API needed for MVP)
 */
class ConversationEngine(
    private val seniorName: String = Constants.DEMO_SENIOR_NAME
) {

    private var conversationStep = 0
    private val conversationHistory = mutableListOf<String>()

    /**
     * Conversation states
     */
    enum class State {
        GREETING,
        SLEEP_QUESTION,
        FEELING_QUESTION,
        PAIN_QUESTION,
        MEDICATION_QUESTION,
        CLOSING
    }

    private var currentState = State.GREETING

    /**
     * Get the next prompt based on current state
     */
    fun getNextPrompt(): String {
        return when (currentState) {
            State.GREETING -> {
                val greeting = DateTimeUtils.getGreeting()
                val timeSpecific = if (DateTimeUtils.isMorning()) {
                    "How did you sleep last night?"
                } else {
                    "How has your day been?"
                }
                "$greeting, $seniorName! $timeSpecific"
            }
            State.SLEEP_QUESTION -> {
                if (DateTimeUtils.isMorning()) {
                    "How did you sleep last night?"
                } else {
                    "How was your day today?"
                }
            }
            State.FEELING_QUESTION -> "How are you feeling right now?"
            State.PAIN_QUESTION -> "Do you have any pain or discomfort?"
            State.MEDICATION_QUESTION -> "Did you take your medicine today?"
            State.CLOSING -> {
                if (DateTimeUtils.isMorning()) {
                    "Great! Have a wonderful day, $seniorName!"
                } else {
                    "Thank you, $seniorName! Have a good evening!"
                }
            }
        }
    }

    /**
     * Process user response and move to next state
     * Returns the bot's response
     */
    fun processResponse(userResponse: String): String {
        // Add to conversation history
        conversationHistory.add("User: $userResponse")

        val lowerResponse = userResponse.lowercase()

        // Generate response based on current state
        val botResponse = when (currentState) {
            State.GREETING -> {
                // Move to next question
                currentState = State.FEELING_QUESTION
                analyzeInitialResponse(lowerResponse)
            }
            State.SLEEP_QUESTION -> {
                currentState = State.FEELING_QUESTION
                analyzeInitialResponse(lowerResponse)
            }
            State.FEELING_QUESTION -> {
                currentState = State.PAIN_QUESTION
                analyzeFeelingResponse(lowerResponse)
            }
            State.PAIN_QUESTION -> {
                currentState = State.MEDICATION_QUESTION
                analyzePainResponse(lowerResponse)
            }
            State.MEDICATION_QUESTION -> {
                currentState = State.CLOSING
                analyzeMedicationResponse(lowerResponse)
            }
            State.CLOSING -> {
                "Thank you for checking in!"
            }
        }

        conversationHistory.add("Bot: $botResponse")
        conversationStep++

        return botResponse
    }

    /**
     * Analyze initial greeting response
     */
    private fun analyzeInitialResponse(response: String): String {
        return when {
            response.contains("good") || response.contains("great") || response.contains("fine") ->
                "That's wonderful to hear!"
            response.contains("okay") || response.contains("alright") ->
                "I'm glad you're doing okay."
            response.contains("not good") || response.contains("bad") || response.contains("tired") ->
                "I'm sorry to hear that. Let's check how you're feeling."
            else -> "I see. Let me ask you a few more questions."
        }
    }

    /**
     * Analyze feeling response
     */
    private fun analyzeFeelingResponse(response: String): String {
        return when {
            response.contains("good") || response.contains("fine") || response.contains("well") ->
                "That's great! Now, tell me..."
            response.contains("not") || response.contains("bad") || response.contains("sick") ->
                "I'm sorry you're not feeling well. Let me ask..."
            response.contains("tired") || response.contains("weak") ->
                "I understand you're feeling tired. Now..."
            else -> "I see. Let me check..."
        }
    }

    /**
     * Analyze pain response
     */
    private fun analyzePainResponse(response: String): String {
        return when {
            response.contains("no") || response.contains("none") || response.contains("not") ->
                "Good, no pain. That's excellent."
            response.contains("yes") || response.contains("pain") || response.contains("hurt") ->
                "I'm noting that you have some pain. I'll let your family know."
            response.contains("little") || response.contains("bit") ->
                "A little pain noted. I'll keep track of that."
            else -> "Okay, I've noted that."
        }
    }

    /**
     * Analyze medication response
     */
    private fun analyzeMedicationResponse(response: String): String {
        return when {
            response.contains("yes") || response.contains("took") || response.contains("taken") ->
                "Excellent! You took your medicine. Well done!"
            response.contains("no") || response.contains("not") || response.contains("forgot") ->
                "Please remember to take your medicine. It's important!"
            response.contains("will") || response.contains("soon") ->
                "Okay, please take it soon. Don't forget!"
            else -> "Alright, I've noted that."
        }
    }

    /**
     * Check if conversation is complete
     */
    fun isComplete(): Boolean {
        return currentState == State.CLOSING && conversationStep > 4
    }

    /**
     * Get full conversation transcript
     */
    fun getTranscript(): String {
        return conversationHistory.joinToString("\n")
    }

    /**
     * Analyze conversation for wellness indicators
     * Returns simple wellness assessment
     */
    fun analyzeWellness(): WellnessAssessment {
        val transcript = getTranscript().lowercase()

        val positiveWords = listOf("good", "great", "fine", "well", "excellent", "wonderful")
        val negativeWords = listOf("bad", "not good", "pain", "hurt", "sick", "tired", "weak", "dizzy")

        val positiveCount = positiveWords.count { transcript.contains(it) }
        val negativeCount = negativeWords.count { transcript.contains(it) }

        val hasPain = transcript.contains("pain") || transcript.contains("hurt")
        val tookMedication = transcript.contains("took") || transcript.contains("taken") || transcript.contains("yes") && transcript.contains("medicine")

        val wellnessScore = when {
            negativeCount >= 3 || hasPain -> 60 // Fair
            negativeCount >= 1 -> 75 // Good
            positiveCount >= 2 -> 90 // Excellent
            else -> 80 // Good
        }

        val status = when {
            wellnessScore >= 85 -> "good"
            wellnessScore >= 70 -> "fair"
            else -> "poor"
        }

        val concerns = mutableListOf<String>()
        if (hasPain) concerns.add("pain reported")
        if (!tookMedication) concerns.add("medication not confirmed")
        if (transcript.contains("dizzy")) concerns.add("dizziness")
        if (transcript.contains("tired")) concerns.add("fatigue")

        return WellnessAssessment(
            score = wellnessScore,
            status = status,
            concerns = concerns,
            tookMedication = tookMedication
        )
    }

    /**
     * Reset conversation for new check-in
     */
    fun reset() {
        conversationStep = 0
        currentState = State.GREETING
        conversationHistory.clear()
    }
}

/**
 * Wellness assessment data class
 */
data class WellnessAssessment(
    val score: Int,
    val status: String,
    val concerns: List<String>,
    val tookMedication: Boolean
)
