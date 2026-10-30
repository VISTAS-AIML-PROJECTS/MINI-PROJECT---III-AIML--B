package com.genvoice.caregiver.viewmodels

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.models.Emergency
import com.genvoice.caregiver.data.models.EmergencyAlertResponse
import com.genvoice.caregiver.data.repository.EmergencyRepository
import com.genvoice.caregiver.utils.Constants
import com.genvoice.caregiver.utils.KeywordDetector
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for emergency operations
 */
class EmergencyViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = EmergencyRepository()

    // Emergency state
    private val _isEmergencyActive = MutableStateFlow(false)
    val isEmergencyActive: StateFlow<Boolean> = _isEmergencyActive.asStateFlow()

    private val _emergencyAlert = MutableStateFlow<EmergencyAlertResponse?>(null)
    val emergencyAlert: StateFlow<EmergencyAlertResponse?> = _emergencyAlert.asStateFlow()

    // Emergency history
    private val _emergencyHistory = MutableStateFlow<List<Emergency>>(emptyList())
    val emergencyHistory: StateFlow<List<Emergency>> = _emergencyHistory.asStateFlow()

    // Active emergencies count
    private val _activeEmergenciesCount = MutableStateFlow(0)
    val activeEmergenciesCount: StateFlow<Int> = _activeEmergenciesCount.asStateFlow()

    // Loading and error states
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    /**
     * Trigger manual emergency (SOS button pressed)
     */
    fun triggerManualEmergency() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            when (val result = repository.triggerManualEmergency(
                seniorId = Constants.DEMO_SENIOR_ID,
                description = "Emergency button pressed by user"
            )) {
                is Result.Success -> {
                    _emergencyAlert.value = result.data
                    _isEmergencyActive.value = true
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
     * Detect emergency from speech text
     */
    fun checkForEmergencyKeywords(text: String): Boolean {
        val (detected, severity) = KeywordDetector.detectEmergency(text)

        if (detected && !KeywordDetector.isFalsePositive(text)) {
            // Emergency detected
            triggerKeywordEmergency(text, severity)
            return true
        }

        return false
    }

    /**
     * Trigger keyword-detected emergency
     */
    private fun triggerKeywordEmergency(detectedText: String, severity: String) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            val description = KeywordDetector.extractEmergencyContext(detectedText)

            when (val result = repository.triggerKeywordEmergency(
                seniorId = Constants.DEMO_SENIOR_ID,
                severity = severity,
                description = description,
                detectedText = detectedText
            )) {
                is Result.Success -> {
                    _emergencyAlert.value = result.data
                    _isEmergencyActive.value = true
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
     * Load emergency history
     */
    fun loadEmergencyHistory(limit: Int = 10) {
        viewModelScope.launch {
            _isLoading.value = true
            when (val result = repository.getEmergencyHistory(Constants.DEMO_SENIOR_ID, limit)) {
                is Result.Success -> {
                    _emergencyHistory.value = result.data
                    // Count active emergencies
                    val activeCount = result.data.count { it.status == "active" }
                    _activeEmergenciesCount.value = activeCount
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
     * Get confirmation message for severity level
     */
    fun getConfirmationMessage(severity: String): String {
        return KeywordDetector.getConfirmationMessage(severity)
    }

    /**
     * Get alert sent message
     */
    fun getAlertSentMessage(): String {
        return KeywordDetector.getAlertSentMessage()
    }

    /**
     * Check if family was notified
     */
    fun wasFamilyNotified(): Boolean {
        return _emergencyAlert.value?.familyNotified == true
    }

    /**
     * Check if SMS was sent
     */
    fun wasSmsSent(): Boolean {
        return _emergencyAlert.value?.smsSent == true
    }

    /**
     * Clear emergency alert state
     */
    fun clearEmergencyAlert() {
        _isEmergencyActive.value = false
        _emergencyAlert.value = null
    }

    /**
     * Clear error
     */
    fun clearError() {
        _error.value = null
    }

    /**
     * Refresh emergency data
     */
    fun refresh() {
        loadEmergencyHistory()
    }
}
