package com.genvoice.caregiver.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.genvoice.caregiver.data.models.Dashboard
import com.genvoice.caregiver.services.VoiceState
import com.genvoice.caregiver.ui.components.*
import com.genvoice.caregiver.ui.theme.OnBackground
import com.genvoice.caregiver.ui.theme.TextSecondary
import com.genvoice.caregiver.utils.DateTimeUtils

/**
 * Home screen - main landing screen
 * Shows big voice button and status overview
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    seniorName: String,
    dashboard: Dashboard?,
    voiceState: VoiceState,
    isBackendConnected: Boolean,
    onVoiceButtonClick: () -> Unit,
    onEmergencyClick: () -> Unit,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "${DateTimeUtils.getGreeting()}, $seniorName!",
                            style = MaterialTheme.typography.titleLarge
                        )
                        if (!isBackendConnected) {
                            Text(
                                text = "Offline",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = onRefresh) {
                        Icon(
                            imageVector = Icons.Filled.Refresh,
                            contentDescription = "Refresh"
                        )
                    }
                }
            )
        },
        bottomBar = {
            CompactEmergencyButton(onClick = onEmergencyClick)
        }
    ) { paddingValues ->
        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(scrollState),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(32.dp))

            // Main voice button
            BigVoiceButton(
                voiceState = voiceState,
                onClick = onVoiceButtonClick,
                enabled = isBackendConnected,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Connection warning
            if (!isBackendConnected) {
                InfoCard(
                    message = "Cannot connect to server. Some features may not work.",
                    icon = Icons.Filled.CloudOff,
                    color = MaterialTheme.colorScheme.error
                )
            }

            // Dashboard status cards
            if (dashboard != null) {
                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "Your Status",
                    style = MaterialTheme.typography.headlineSmall,
                    color = OnBackground,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp)
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Wellness card
                WellnessStatusCard(
                    wellnessScore = dashboard.wellness.overallScore,
                    wellnessStatus = dashboard.wellness.status
                )

                // Check-in card
                CheckInStatusCard(
                    completionRate = dashboard.checkIns.completionRate ?: 0f,
                    lastCheckIn = dashboard.checkIns.lastCheckIn
                )

                // Medication card
                dashboard.medications.compliance?.let { compliance ->
                    MedicationStatusCard(
                        complianceRate = compliance.rate,
                        medicationCount = dashboard.medications.count
                    )
                }

                // Emergency status (if any active)
                if ((dashboard.emergencies.activeCount ?: 0) > 0) {
                    InfoCard(
                        message = "You have ${dashboard.emergencies.activeCount} active emergency alert(s)",
                        icon = Icons.Filled.Warning,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Premium Elegant Tip Card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                ),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(
                    defaultElevation = 4.dp
                )
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(20.dp),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Gold accent circle
                    Canvas(
                        modifier = Modifier
                            .size(40.dp)
                            .align(Alignment.Top)
                    ) {
                        drawCircle(
                            color = Color(0xFFD4AF37),  // Royal Gold
                            radius = size.minDimension / 2
                        )
                    }

                    // Content
                    Column(
                        modifier = Modifier.weight(1f),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "Welcome to GenVoice",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.SemiBold,
                            color = MaterialTheme.colorScheme.primary,
                            letterSpacing = 0.5.sp
                        )
                        Text(
                            text = "Tap the voice button above to start your daily check-in. I'll have a friendly conversation with you about your wellbeing.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.85f),
                            lineHeight = 24.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}
