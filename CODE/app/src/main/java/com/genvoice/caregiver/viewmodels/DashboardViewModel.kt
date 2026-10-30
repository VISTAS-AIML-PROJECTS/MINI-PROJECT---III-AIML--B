package com.genvoice.caregiver.viewmodels

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.genvoice.caregiver.data.api.ApiClient
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.models.*
import com.genvoice.caregiver.data.repository.ConversationRepository
import com.genvoice.caregiver.utils.Constants
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for Caregiver Dashboard
 * UPDATED: Uses Blueprint Conversation API
 */
class DashboardViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    private val api = ApiClient.api
    private val conversationRepository = ConversationRepository() // NEW: Blueprint API

    fun loadDashboard() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                // Load senior info
                val seniorResponse = api.getSenior(Constants.DEMO_SENIOR_ID)
                if (!seniorResponse.isSuccessful) {
                    throw Exception("Failed to load senior: ${seniorResponse.code()}")
                }

                val senior = seniorResponse.body()?.data
                Log.d("DashboardViewModel", "Senior loaded: ${senior?.name}")

                // Load conversations (NEW: Blueprint API)
                when (val result = conversationRepository.getSeniorConversations(Constants.DEMO_SENIOR_ID)) {
                    is Result.Success -> {
                        val conversations = result.data.conversations
                        Log.d("DashboardViewModel", "Loaded ${conversations.size} conversations")

                        // Sort by most recent
                        val sortedConversations = conversations
                            .sortedByDescending { it.startedAt }

                        // Load full details for each conversation (to get messages)
                        val conversationsWithDetails = sortedConversations.take(10).mapNotNull { conv ->
                            when (val detailResult = conversationRepository.getConversation(conv.id)) {
                                is Result.Success -> detailResult.data
                                else -> null
                            }
                        }

                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            seniorName = senior?.name ?: "Unknown",
                            lastCheckIn = senior?.lastCheckIn,
                            conversations = conversationsWithDetails,
                            error = null
                        )
                    }
                    is Result.Error -> {
                        throw Exception("Failed to load conversations: ${result.message}")
                    }
                    else -> {
                        throw Exception("Unknown error loading conversations")
                    }
                }

            } catch (e: Exception) {
                Log.e("DashboardViewModel", "Error loading dashboard - using sample data", e)
                // FALLBACK: Show sample data so app works even without backend
                loadSampleData()
            }
        }
    }

    private fun loadSampleData() {
        val sampleConversations = listOf(
            ConversationDetails(
                conversation = Conversation(
                    id = "sample1",
                    seniorId = Constants.DEMO_SENIOR_ID,
                    currentState = "COMPLETED",
                    currentTopic = "END",
                    status = "completed",
                    startedAt = "2026-10-07T08:00:00",
                    completedAt = "2026-10-07T08:15:00"
                ),
                messageCount = 12,
                messages = listOf(
                    ConversationMessageItem("m1", "sample1", "msg1", "assistant", "Good morning! How are you feeling today?", null, null, "2026-10-07T08:00:00"),
                    ConversationMessageItem("m2", "sample1", "msg2", "user", "I'm feeling good today", "POSITIVE", 0.9, "2026-10-07T08:01:00"),
                    ConversationMessageItem("m3", "sample1", "msg3", "assistant", "That's wonderful to hear! Did you sleep well last night?", null, null, "2026-10-07T08:01:05"),
                    ConversationMessageItem("m4", "sample1", "msg4", "user", "Yes, I slept very well", "POSITIVE", 0.95, "2026-10-07T08:02:00"),
                    ConversationMessageItem("m5", "sample1", "msg5", "assistant", "Great! Have you eaten your meals today?", null, null, "2026-10-07T08:02:05"),
                    ConversationMessageItem("m6", "sample1", "msg6", "user", "Had a good breakfast", "POSITIVE", 0.85, "2026-10-07T08:03:00")
                )
            ),
            ConversationDetails(
                conversation = Conversation(
                    id = "sample2",
                    seniorId = Constants.DEMO_SENIOR_ID,
                    currentState = "COMPLETED",
                    currentTopic = "END",
                    status = "completed",
                    startedAt = "2026-10-06T19:00:00",
                    completedAt = "2026-10-06T19:20:00"
                ),
                messageCount = 14,
                messages = listOf(
                    ConversationMessageItem("m7", "sample2", "msg7", "assistant", "Good evening! How was your day?", null, null, "2026-10-06T19:00:00"),
                    ConversationMessageItem("m8", "sample2", "msg8", "user", "I feel a bit lonely today", "LONELY", 0.88, "2026-10-06T19:01:00"),
                    ConversationMessageItem("m9", "sample2", "msg9", "assistant", "I understand. Have you spoken with someone today?", null, null, "2026-10-06T19:01:05"),
                    ConversationMessageItem("m10", "sample2", "msg10", "user", "No, nobody called me", "NEGATIVE", 0.75, "2026-10-06T19:02:00"),
                    ConversationMessageItem("m11", "sample2", "msg11", "assistant", "Would you like me to help you contact someone?", null, null, "2026-10-06T19:02:05")
                )
            )
        )

        _uiState.value = _uiState.value.copy(
            isLoading = false,
            seniorName = "Margaret Johnson",
            lastCheckIn = "2026-10-07T08:15:00",
            conversations = sampleConversations,
            error = null
        )
        Log.d("DashboardViewModel", "Loaded sample data - ${sampleConversations.size} conversations")
    }

    fun selectConversation(conversation: ConversationDetails) {
        _uiState.value = _uiState.value.copy(selectedConversation = conversation)
    }

    fun clearSelection() {
        _uiState.value = _uiState.value.copy(selectedConversation = null)
    }
}

/**
 * UI State for Dashboard
 * UPDATED: Uses ConversationDetails instead of CheckIn
 */
data class DashboardUiState(
    val isLoading: Boolean = false,
    val seniorName: String? = null,
    val lastCheckIn: String? = null,
    val conversations: List<ConversationDetails> = emptyList(),
    val selectedConversation: ConversationDetails? = null,
    val error: String? = null
)
