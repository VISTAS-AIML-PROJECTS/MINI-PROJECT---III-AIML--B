package com.genvoice.caregiver.viewmodels

import android.app.Application
import android.media.ToneGenerator
import android.media.AudioManager
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.models.Dashboard
import com.genvoice.caregiver.data.models.Senior
import com.genvoice.caregiver.data.repository.SeniorRepository
import com.genvoice.caregiver.services.VoiceService
import com.genvoice.caregiver.services.VoiceState
import com.genvoice.caregiver.utils.Constants
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Main ViewModel for overall app state
 */
class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val seniorRepository = SeniorRepository()
    private val voiceService = VoiceService(application)

    // Simple tone generator for listening beep
    private val toneGenerator = ToneGenerator(AudioManager.STREAM_ALARM, 100)

    // Current senior (hardcoded for demo)
    private val _senior = MutableStateFlow<Senior?>(null)
    val senior: StateFlow<Senior?> = _senior.asStateFlow()

    // Dashboard data
    private val _dashboard = MutableStateFlow<Dashboard?>(null)
    val dashboard: StateFlow<Dashboard?> = _dashboard.asStateFlow()

    // App state
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    private val _isBackendConnected = MutableStateFlow(false)
    val isBackendConnected: StateFlow<Boolean> = _isBackendConnected.asStateFlow()

    // Voice state
    private val _voiceState = MutableStateFlow(VoiceState.IDLE)
    val voiceState: StateFlow<VoiceState> = _voiceState.asStateFlow()

    private val _isVoiceReady = MutableStateFlow(false)
    val isVoiceReady: StateFlow<Boolean> = _isVoiceReady.asStateFlow()

    init {
        initializeVoice()
        checkBackendConnection()
        loadSeniorProfile()
    }

    /**
     * Initialize voice service
     */
    private fun initializeVoice() {
        voiceService.apply {
            // Set up callbacks
            onTtsStart = {
                _voiceState.value = VoiceState.SPEAKING
            }
            onTtsComplete = {
                _voiceState.value = VoiceState.IDLE
            }
            onSpeechStart = {
                _voiceState.value = VoiceState.LISTENING
                // Play short beep sound to indicate listening started
                playListeningBeep()
            }
            onSpeechEnd = {
                _voiceState.value = VoiceState.PROCESSING
            }
            onSpeechError = { error ->
                _error.value = error
                _voiceState.value = VoiceState.ERROR
            }

            // Initialize
            initialize {
                _isVoiceReady.value = true
            }
        }
    }

    /**
     * Check backend connection
     */
    private fun checkBackendConnection() {
        viewModelScope.launch {
            val isConnected = seniorRepository.checkBackendHealth()
            _isBackendConnected.value = isConnected
            if (!isConnected) {
                _error.value = "Cannot connect to backend. Please check if server is running."
            }
        }
    }

    /**
     * Load senior profile
     */
    private fun loadSeniorProfile() {
        viewModelScope.launch {
            _isLoading.value = true
            when (val result = seniorRepository.getSenior(Constants.DEMO_SENIOR_ID)) {
                is Result.Success -> {
                    _senior.value = result.data
                    loadDashboard()
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
     * Load dashboard data
     */
    fun loadDashboard() {
        viewModelScope.launch {
            _isLoading.value = true
            when (val result = seniorRepository.getDashboard(Constants.DEMO_SENIOR_ID)) {
                is Result.Success -> {
                    _dashboard.value = result.data
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
     * Speak text
     */
    fun speak(text: String) {
        voiceService.speak(text)
    }

    /**
     * Start listening
     */
    fun startListening(onResult: (String) -> Unit) {
        voiceService.onSpeechResult = onResult
        voiceService.startListening()
    }

    /**
     * Stop listening
     */
    fun stopListening() {
        voiceService.stopListening()
    }

    /**
     * Get voice service instance
     */
    fun getVoiceService(): VoiceService {
        return voiceService
    }

    /**
     * Clear error
     */
    fun clearError() {
        _error.value = null
        _voiceState.value = VoiceState.IDLE
    }

    /**
     * Reset voice state to idle
     */
    fun resetVoiceState() {
        _voiceState.value = VoiceState.IDLE
    }

    /**
     * Refresh all data
     */
    fun refresh() {
        checkBackendConnection()
        loadSeniorProfile()
    }

    /**
     * Play a simple, audible beep when listening starts
     * Double beep for clear audio feedback
     */
    private fun playListeningBeep() {
        viewModelScope.launch {
            try {
                // Play two short beeps (phone keypad tone - always audible)
                toneGenerator.startTone(ToneGenerator.TONE_DTMF_1, 150)
                kotlinx.coroutines.delay(100)
                toneGenerator.startTone(ToneGenerator.TONE_DTMF_1, 150)
            } catch (e: Exception) {
                // Ignore if sound fails
            }
        }
    }

    /**
     * Cleanup
     */
    override fun onCleared() {
        super.onCleared()
        voiceService.shutdown()
        toneGenerator.release()
    }
}
