package com.genvoice.caregiver.services

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import com.genvoice.caregiver.utils.Constants
import kotlinx.coroutines.suspendCancellableCoroutine
import java.util.*
import kotlin.coroutines.resume

/**
 * Voice Service for Speech-to-Text and Text-to-Speech
 * Optimized for elderly users
 */
class VoiceService(private val context: Context) {

    companion object {
        private const val TAG = "VoiceService"
        private const val UTTERANCE_ID = "genvoice_utterance"
    }

    // Text-to-Speech engine
    private var tts: TextToSpeech? = null
    private var isTtsReady = false

    // Speech-to-Text recognizer
    private var speechRecognizer: SpeechRecognizer? = null
    private var isListening = false

    // Callbacks
    var onSpeechResult: ((String) -> Unit)? = null
    var onSpeechError: ((String) -> Unit)? = null
    var onSpeechStart: (() -> Unit)? = null
    var onSpeechEnd: (() -> Unit)? = null
    var onTtsStart: (() -> Unit)? = null
    var onTtsComplete: (() -> Unit)? = null

    /**
     * Initialize the voice service
     */
    fun initialize(onReady: () -> Unit) {
        initializeTts(onReady)
        initializeSpeechRecognizer()
    }

    /**
     * Initialize Text-to-Speech
     */
    private fun initializeTts(onReady: () -> Unit) {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.apply {
                    // Set language
                    val result = setLanguage(Locale.US)
                    if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                        Log.e(TAG, "TTS language not supported")
                        onSpeechError?.invoke("Text-to-Speech language not available")
                    } else {
                        // Set elderly-optimized settings
                        setSpeechRate(Constants.TTS_SPEED) // 15% slower
                        setPitch(Constants.TTS_PITCH) // Normal pitch

                        // Set utterance progress listener
                        setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                            override fun onStart(utteranceId: String?) {
                                Log.d(TAG, "TTS started speaking")
                                onTtsStart?.invoke()
                            }

                            override fun onDone(utteranceId: String?) {
                                Log.d(TAG, "TTS finished speaking")
                                onTtsComplete?.invoke()
                            }

                            @Deprecated("Deprecated in Java")
                            override fun onError(utteranceId: String?) {
                                Log.e(TAG, "TTS error")
                                onSpeechError?.invoke("Speech output error")
                            }
                        })

                        isTtsReady = true
                        Log.d(TAG, "TTS initialized successfully")
                        onReady()
                    }
                }
            } else {
                Log.e(TAG, "TTS initialization failed")
                onSpeechError?.invoke("Text-to-Speech initialization failed")
            }
        }
    }

    /**
     * Initialize Speech Recognizer
     */
    private fun initializeSpeechRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            Log.e(TAG, "Speech recognition not available")
            onSpeechError?.invoke("Speech recognition not available on this device")
            return
        }

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                Log.d(TAG, "Ready for speech")
                isListening = true
                onSpeechStart?.invoke()
            }

            override fun onBeginningOfSpeech() {
                Log.d(TAG, "User started speaking")
            }

            override fun onRmsChanged(rmsdB: Float) {
                // Audio level changed - can be used for visualization
            }

            override fun onBufferReceived(buffer: ByteArray?) {
                // Partial audio buffer
            }

            override fun onEndOfSpeech() {
                Log.d(TAG, "User stopped speaking")
                isListening = false
                onSpeechEnd?.invoke()
            }

            override fun onError(error: Int) {
                isListening = false
                val errorMessage = getErrorMessage(error)
                Log.e(TAG, "Speech recognition error: $errorMessage")
                onSpeechError?.invoke(errorMessage)
            }

            override fun onResults(results: Bundle?) {
                isListening = false
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    val recognizedText = matches[0]
                    Log.d(TAG, "Recognized: $recognizedText")
                    onSpeechResult?.invoke(recognizedText)
                } else {
                    Log.e(TAG, "No speech results")
                    onSpeechError?.invoke("I didn't hear anything. Please try again.")
                }
            }

            override fun onPartialResults(partialResults: Bundle?) {
                // Partial results available (real-time transcription)
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    Log.d(TAG, "Partial: ${matches[0]}")
                    // Could update UI with partial results here
                }
            }

            override fun onEvent(eventType: Int, params: Bundle?) {
                // Recognition event
            }
        })

        Log.d(TAG, "Speech recognizer initialized")
    }

    /**
     * Speak text using TTS
     */
    fun speak(text: String) {
        if (!isTtsReady) {
            Log.e(TAG, "TTS not ready")
            onSpeechError?.invoke("Voice output not ready")
            return
        }

        // Stop any current speech
        stopSpeaking()

        // Speak the text
        val params = Bundle().apply {
            putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, UTTERANCE_ID)
        }

        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, params, UTTERANCE_ID)
        Log.d(TAG, "Speaking: $text")
    }

    /**
     * Speak text and wait for completion (suspending function)
     */
    suspend fun speakAndWait(text: String): Boolean = suspendCancellableCoroutine { continuation ->
        if (!isTtsReady) {
            continuation.resume(false)
            return@suspendCancellableCoroutine
        }

        // Set up one-time completion listener
        val originalListener = onTtsComplete
        onTtsComplete = {
            onTtsComplete = originalListener // Restore original listener
            continuation.resume(true)
        }

        // Cancel if coroutine is cancelled
        continuation.invokeOnCancellation {
            stopSpeaking()
            onTtsComplete = originalListener
        }

        speak(text)
    }

    /**
     * Start listening for speech
     */
    fun startListening() {
        if (isListening) {
            Log.w(TAG, "Already listening")
            return
        }

        // Stop any current speech first
        stopSpeaking()

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.US)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)

            // FIXED: Increased timeouts for elderly with quiet/slow speech
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, Constants.STT_TIMEOUT_MS)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, Constants.STT_TIMEOUT_MS)

            // REMOVED: Minimum length was causing detection delays
            // REMOVED: Offline preference - use online for better recognition

            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }

        try {
            speechRecognizer?.startListening(intent)
            Log.d(TAG, "Started listening")
        } catch (e: Exception) {
            Log.e(TAG, "Error starting speech recognition", e)
            onSpeechError?.invoke("Could not start listening: ${e.message}")
        }
    }

    /**
     * Stop listening for speech
     */
    fun stopListening() {
        if (isListening) {
            speechRecognizer?.stopListening()
            isListening = false
            Log.d(TAG, "Stopped listening")
        }
    }

    /**
     * Cancel listening (immediate stop)
     */
    fun cancelListening() {
        if (isListening) {
            speechRecognizer?.cancel()
            isListening = false
            Log.d(TAG, "Cancelled listening")
        }
    }

    /**
     * Stop speaking
     */
    fun stopSpeaking() {
        tts?.stop()
    }

    /**
     * Check if currently speaking
     */
    fun isSpeaking(): Boolean {
        return tts?.isSpeaking ?: false
    }

    /**
     * Check if currently listening
     */
    fun isListening(): Boolean {
        return isListening
    }

    /**
     * Check if TTS is ready
     */
    fun isTtsReady(): Boolean {
        return isTtsReady
    }

    /**
     * Cleanup resources
     */
    fun shutdown() {
        stopListening()
        stopSpeaking()

        speechRecognizer?.destroy()
        speechRecognizer = null

        tts?.shutdown()
        tts = null

        isTtsReady = false
        isListening = false

        Log.d(TAG, "Voice service shut down")
    }

    /**
     * Get user-friendly error message
     */
    private fun getErrorMessage(errorCode: Int): String {
        return when (errorCode) {
            SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
            SpeechRecognizer.ERROR_CLIENT -> "Client error"
            SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission denied"
            SpeechRecognizer.ERROR_NETWORK -> "Network error"
            SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
            SpeechRecognizer.ERROR_NO_MATCH -> "I didn't catch that. Could you say it again?"
            SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Speech recognizer busy"
            SpeechRecognizer.ERROR_SERVER -> "Server error"
            SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "I didn't hear anything. Please try again."
            else -> "Speech recognition error"
        }
    }
}

/**
 * Voice interaction state
 */
enum class VoiceState {
    IDLE,           // Not doing anything
    SPEAKING,       // TTS is speaking
    LISTENING,      // STT is listening
    PROCESSING,     // Processing speech result
    ERROR           // Error occurred
}
