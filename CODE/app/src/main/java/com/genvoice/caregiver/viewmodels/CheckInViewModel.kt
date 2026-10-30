package com.genvoice.caregiver.viewmodels

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.models.*
import com.genvoice.caregiver.data.repository.CheckInRepository
import com.genvoice.caregiver.utils.Constants
import com.genvoice.caregiver.utils.DateTimeUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for check-in operations
 */
class CheckInViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = CheckInRepository()

    // Conversation history for AI
    private val _conversationHistory = MutableStateFlow<List<ConversationMessage>>(emptyList())
    val conversationHistory: StateFlow<List<ConversationMessage>> = _conversationHistory.asStateFlow()

    // Check-in state
    private val _isCheckingIn = MutableStateFlow(false)
    val isCheckingIn: StateFlow<Boolean> = _isCheckingIn.asStateFlow()

    private val _currentCheckInId = MutableStateFlow<String?>(null)
    val currentCheckInId: StateFlow<String?> = _currentCheckInId.asStateFlow()

    private val _currentPrompt = MutableStateFlow<String?>(null)
    val currentPrompt: StateFlow<String?> = _currentPrompt.asStateFlow()

    private val _checkInComplete = MutableStateFlow(false)
    val checkInComplete: StateFlow<Boolean> = _checkInComplete.asStateFlow()

    private val _checkInResult = MutableStateFlow<CheckInSubmitResponse?>(null)
    val checkInResult: StateFlow<CheckInSubmitResponse?> = _checkInResult.asStateFlow()

    // Check-in history
    private val _checkInHistory = MutableStateFlow<List<CheckIn>>(emptyList())
    val checkInHistory: StateFlow<List<CheckIn>> = _checkInHistory.asStateFlow()

    // Loading and error states
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    // Scheduling state
    private val _showScheduleDialog = MutableStateFlow(false)
    val showScheduleDialog: StateFlow<Boolean> = _showScheduleDialog.asStateFlow()

    private val _aiOfferingSchedule = MutableStateFlow(false)
    val aiOfferingSchedule: StateFlow<Boolean> = _aiOfferingSchedule.asStateFlow()

    /**
     * Start a new check-in with AI conversation
     */
    fun startCheckIn() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            // Determine check-in type based on time
            val checkInType = DateTimeUtils.getCurrentCheckInType()

            // Start check-in via API
            when (val result = repository.startCheckIn(Constants.DEMO_SENIOR_ID, checkInType)) {
                is Result.Success -> {
                    _currentCheckInId.value = result.data.checkInId
                    _isCheckingIn.value = true
                    _checkInComplete.value = false

                    // Clear conversation history
                    _conversationHistory.value = emptyList()

                    // Get first AI greeting
                    getAiGreeting()
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
            _isLoading.value = false
        }
    }

    /**
     * Get AI greeting (first message)
     */
    private fun getAiGreeting() {
        viewModelScope.launch {
            when (val result = repository.getAiConversationResponse(
                userMessage = null,
                conversationHistory = emptyList(),
                isFirstMessage = true,
                seniorName = Constants.DEMO_SENIOR_NAME
            )) {
                is Result.Success -> {
                    val greeting = result.data.aiResponse
                    _currentPrompt.value = greeting

                    // Add to conversation history
                    _conversationHistory.value = listOf(
                        ConversationMessage(role = "assistant", content = greeting)
                    )
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
        }
    }

    /**
     * Process user response and get AI response
     */
    suspend fun processResponseWithAi(userResponse: String): String {
        // Add user message to history
        val currentHistory = _conversationHistory.value.toMutableList()
        currentHistory.add(ConversationMessage(role = "user", content = userResponse))

        // Get AI response
        return when (val result = repository.getAiConversationResponse(
            userMessage = userResponse,
            conversationHistory = _conversationHistory.value,
            isFirstMessage = false,
            seniorName = Constants.DEMO_SENIOR_NAME
        )) {
            is Result.Success -> {
                val aiResponse = result.data.aiResponse
                val isComplete = result.data.conversationComplete
                val offeringSchedule = result.data.offeringSchedule

                // Add AI response to history
                currentHistory.add(ConversationMessage(role = "assistant", content = aiResponse))
                _conversationHistory.value = currentHistory

                // Update current prompt
                _currentPrompt.value = aiResponse

                // Check if AI is offering to schedule
                if (offeringSchedule) {
                    _aiOfferingSchedule.value = true
                    _showScheduleDialog.value = true
                }

                // Check if conversation is complete
                if (isComplete) {
                    // Set complete immediately so UI updates
                    _checkInComplete.value = true
                    _isCheckingIn.value = false

                    // Submit in background
                    submitCheckIn()
                }

                aiResponse
            }
            is Result.Error -> {
                _error.value = result.message
                "I'm sorry, could you say that again?"
            }
            else -> "I'm sorry, could you say that again?"
        }
    }

    /**
     * Submit completed check-in
     */
    private fun submitCheckIn() {
        val checkInId = _currentCheckInId.value ?: return

        viewModelScope.launch {
            _isLoading.value = true

            // Build transcript from conversation history
            val transcript = _conversationHistory.value.joinToString("\n") { msg ->
                "${msg.role.uppercase()}: ${msg.content}"
            }

            // Simple wellness assessment based on keywords
            val transcriptLower = transcript.lowercase()
            val hasNegative = transcriptLower.contains("pain") ||
                              transcriptLower.contains("bad") ||
                              transcriptLower.contains("hurt") ||
                              transcriptLower.contains("sick")

            val wellnessStatus = if (hasNegative) "fair" else "good"
            val wellnessScore = if (hasNegative) 70 else 85
            val concerns = if (hasNegative) "Mentioned discomfort" else null

            // Submit to backend
            when (val result = repository.submitCheckIn(
                checkInId = checkInId,
                seniorId = Constants.DEMO_SENIOR_ID,
                conversationTranscript = transcript,
                wellnessStatus = wellnessStatus,
                wellnessScore = wellnessScore,
                concernsDetected = concerns,
                concernSeverity = if (concerns != null) 5 else null
            )) {
                is Result.Success -> {
                    _checkInResult.value = result.data
                    _checkInComplete.value = true
                    _isCheckingIn.value = false

                    // Clear current check-in
                    _currentCheckInId.value = null
                    _currentPrompt.value = null
                    _conversationHistory.value = emptyList()
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
            _isLoading.value = false
        }
    }

    /**
     * Cancel current check-in
     */
    fun cancelCheckIn() {
        _isCheckingIn.value = false
        _currentCheckInId.value = null
        _currentPrompt.value = null
        _checkInComplete.value = false
        _conversationHistory.value = emptyList()
    }

    /**
     * Load check-in history
     */
    fun loadCheckInHistory(limit: Int = 10) {
        viewModelScope.launch {
            _isLoading.value = true
            when (val result = repository.getCheckInHistory(Constants.DEMO_SENIOR_ID, limit)) {
                is Result.Success -> {
                    _checkInHistory.value = result.data
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
            _isLoading.value = false
        }
    }

    /**
     * Get current conversation step
     */
    fun getCurrentPrompt(): String? {
        return _currentPrompt.value
    }

    /**
     * Check if it's time for morning check-in
     */
    fun isMorningCheckInTime(): Boolean {
        val hour = DateTimeUtils.getCurrentHour()
        return hour == Constants.MORNING_CHECKIN_HOUR
    }

    /**
     * Check if it's time for evening check-in
     */
    fun isEveningCheckInTime(): Boolean {
        val hour = DateTimeUtils.getCurrentHour()
        return hour == Constants.EVENING_CHECKIN_HOUR
    }

    /**
     * Clear error
     */
    fun clearError() {
        _error.value = null
    }

    /**
     * Reset check-in complete state
     */
    fun resetCheckInComplete() {
        _checkInComplete.value = false
        _checkInResult.value = null
    }

    /**
     * Schedule check-in for later
     */
    fun scheduleCheckIn(minutes: Int) {
        viewModelScope.launch {
            _isLoading.value = true

            when (val result = repository.scheduleCheckIn(
                seniorId = Constants.DEMO_SENIOR_ID,
                minutesFromNow = minutes
            )) {
                is Result.Success -> {
                    // Schedule succeeded - cancel current check-in
                    cancelCheckIn()
                    _showScheduleDialog.value = false
                    _aiOfferingSchedule.value = false

                    // Success message will be shown in UI
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }

            _isLoading.value = false
        }
    }

    /**
     * Dismiss schedule dialog
     */
    fun dismissScheduleDialog() {
        _showScheduleDialog.value = false
        _aiOfferingSchedule.value = false
    }
}
