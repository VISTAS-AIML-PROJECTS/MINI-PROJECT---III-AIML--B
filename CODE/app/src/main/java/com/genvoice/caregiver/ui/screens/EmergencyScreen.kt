package com.genvoice.caregiver.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.genvoice.caregiver.data.models.EmergencyAlertResponse
import com.genvoice.caregiver.ui.components.EmergencyAlertCard
import com.genvoice.caregiver.ui.components.EmergencyButton
import com.genvoice.caregiver.ui.components.InfoCard
import com.genvoice.caregiver.ui.theme.OnBackground

/**
 * Emergency screen
 * Shows emergency button and handles emergency alerts
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EmergencyScreen(
    isEmergencyActive: Boolean,
    emergencyAlert: EmergencyAlertResponse?,
    onEmergencyTrigger: () -> Unit,
    onBackClick: () -> Unit,
    onDismissAlert: () -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Emergency",
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
        Box(
            modifier = modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(scrollState),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Spacer(modifier = Modifier.height(32.dp))

                // Instructions
                if (!isEmergencyActive) {
                    Text(
                        text = "Need Help?",
                        style = MaterialTheme.typography.headlineLarge,
                        color = OnBackground
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Text(
                        text = "Press the button below to alert your family immediately",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.padding(horizontal = 32.dp)
                    )

                    Spacer(modifier = Modifier.height(32.dp))
                }

                // Emergency button
                EmergencyButton(
                    onClick = onEmergencyTrigger,
                    isActive = isEmergencyActive
                )

                Spacer(modifier = Modifier.height(24.dp))

                // Info card
                if (!isEmergencyActive) {
                    InfoCard(
                        message = "You can also say 'help' or 'emergency' during a conversation, and I'll automatically alert your family.",
                        icon = Icons.Filled.Info,
                        color = MaterialTheme.colorScheme.primary
                    )
                }

                Spacer(modifier = Modifier.height(32.dp))
            }

            // Emergency alert overlay
            if (emergencyAlert != null && isEmergencyActive) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    contentAlignment = Alignment.Center
                ) {
                    EmergencyAlertCard(
                        message = "Your family has been notified. Help is on the way. Stay calm, someone will be there soon.",
                        onDismiss = onDismissAlert
                    )
                }
            }
        }
    }
}
