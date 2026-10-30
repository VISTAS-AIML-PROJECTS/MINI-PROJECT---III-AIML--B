package com.genvoice.caregiver.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.genvoice.caregiver.data.models.CheckInSubmitResponse
import com.genvoice.caregiver.services.VoiceState
import com.genvoice.caregiver.ui.components.*
import com.genvoice.caregiver.ui.theme.OnBackground
import com.genvoice.caregiver.ui.theme.WellnessGood

/**
 * Conversation screen for check-in interactions
 * Shows conversation flow and visual feedback
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConversationScreen(
    voiceState: VoiceState,
    currentPrompt: String?,
    conversationHistory: List<String>,
    checkInComplete: Boolean,
    checkInResult: CheckInSubmitResponse?,
    onBackClick: () -> Unit,
    onCancelClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = if (checkInComplete) "Check-In Complete!" else "Daily Check-In",
                        style = MaterialTheme.typography.titleLarge
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(
                            imageVector = Icons.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(scrollState),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(24.dp))

            if (checkInComplete && checkInResult != null) {
                // Check-in complete screen
                CheckInCompleteView(
                    result = checkInResult,
                    onDoneClick = onBackClick
                )
            } else {
                // Active conversation
                ActiveConversationView(
                    voiceState = voiceState,
                    currentPrompt = currentPrompt,
                    conversationHistory = conversationHistory,
                    onCancelClick = onCancelClick
                )
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

/**
 * Active conversation view
 */
@Composable
private fun ActiveConversationView(
    voiceState: VoiceState,
    currentPrompt: String?,
    conversationHistory: List<String>,
    onCancelClick: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // FIXED: Single consistent voice state indicator
        when (voiceState) {
            VoiceState.LISTENING -> {
                // Gold mic icon
                Icon(
                    imageVector = Icons.Filled.Mic,
                    contentDescription = "Listening",
                    modifier = Modifier.size(80.dp),
                    tint = MaterialTheme.colorScheme.primary  // Royal Gold
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "I'm listening...",
                    style = MaterialTheme.typography.displayMedium,
                    color = OnBackground
                )
            }
            VoiceState.SPEAKING -> {
                PulsingCircle()
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Speaking...",
                    style = MaterialTheme.typography.titleLarge,
                    color = OnBackground
                )
            }
            VoiceState.PROCESSING -> {
                // Processing is same as listening for user
                Icon(
                    imageVector = Icons.Filled.Mic,
                    contentDescription = "Listening",
                    modifier = Modifier.size(80.dp),
                    tint = MaterialTheme.colorScheme.primary  // Royal Gold
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "I'm listening...",
                    style = MaterialTheme.typography.displayMedium,
                    color = OnBackground
                )
            }
            else -> {
                // Idle or error - show nothing, just wait
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Conversation history (if any)
        if (conversationHistory.isNotEmpty()) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "Conversation:",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    conversationHistory.takeLast(6).forEach { line ->
                        Text(
                            text = line,
                            style = MaterialTheme.typography.bodyMedium,
                            color = OnBackground,
                            modifier = Modifier.padding(vertical = 4.dp)
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Cancel button
        OutlinedButton(
            onClick = onCancelClick,
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
        ) {
            Text(
                text = "Cancel Check-In",
                style = MaterialTheme.typography.titleMedium
            )
        }
    }
}

/**
 * Check-in complete view
 */
@Composable
private fun CheckInCompleteView(
    result: CheckInSubmitResponse,
    onDoneClick: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = Icons.Filled.CheckCircle,
            contentDescription = "Complete",
            modifier = Modifier.size(80.dp),
            tint = WellnessGood
        )

        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = "Check-In Complete!",
            style = MaterialTheme.typography.headlineMedium,
            color = OnBackground
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Wellness score
        WellnessStatusCard(
            wellnessScore = result.wellnessScore.toFloat(),
            wellnessStatus = result.wellnessStatus
        )

        // Concerns (if any)
        if (!result.concernsDetected.isNullOrEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            InfoCard(
                message = "Concerns noted: ${result.concernsDetected.joinToString(", ")}",
                icon = Icons.Filled.Info,
                color = MaterialTheme.colorScheme.tertiary
            )
        }

        // Family notified
        if (result.familyNotified) {
            Spacer(modifier = Modifier.height(16.dp))
            InfoCard(
                message = "Your family has been updated",
                icon = Icons.Filled.CheckCircle,
                color = WellnessGood
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Done button
        Button(
            onClick = onDoneClick,
            modifier = Modifier
                .fillMaxWidth()
                .height(60.dp)
        ) {
            Text(
                text = "Done",
                style = MaterialTheme.typography.titleLarge
            )
        }
    }
}
