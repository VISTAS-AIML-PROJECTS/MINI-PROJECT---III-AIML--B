package com.genvoice.caregiver.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.genvoice.caregiver.ui.theme.Emergency
import com.genvoice.caregiver.ui.theme.OnEmergency

/**
 * Big red emergency button
 * Highly visible, easy to tap in emergency situations
 */
@Composable
fun EmergencyButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    isActive: Boolean = false
) {
    // Pulse animation when active
    val infiniteTransition = rememberInfiniteTransition(label = "emergency_pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp)
            .scale(if (isActive) scale else 1f)
            .clickable(
                onClick = onClick,
                indication = null,
                interactionSource = remember { MutableInteractionSource() }
            ),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = Emergency
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = if (isActive) 12.dp else 8.dp
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = Icons.Filled.Warning,
                contentDescription = "Emergency",
                modifier = Modifier.size(64.dp),
                tint = OnEmergency
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = if (isActive) "ALERTING FAMILY..." else "EMERGENCY",
                style = MaterialTheme.typography.headlineMedium,
                color = OnEmergency
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = if (isActive) "Help is on the way" else "Tap if you need help",
                style = MaterialTheme.typography.bodyLarge,
                color = OnEmergency.copy(alpha = 0.9f)
            )
        }
    }
}

/**
 * Compact emergency button for bottom of screen
 */
@Composable
fun CompactEmergencyButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .background(Emergency)
            .clickable(onClick = onClick)
            .padding(16.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = Icons.Filled.Warning,
                contentDescription = "Emergency",
                tint = OnEmergency,
                modifier = Modifier.size(28.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                text = "EMERGENCY",
                style = MaterialTheme.typography.titleLarge,
                color = OnEmergency
            )
        }
    }
}

/**
 * Emergency alert confirmation dialog
 */
@Composable
fun EmergencyAlertCard(
    message: String,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = Emergency.copy(alpha = 0.95f)
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = 16.dp
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = Icons.Filled.Warning,
                contentDescription = "Emergency Alert",
                modifier = Modifier.size(56.dp),
                tint = OnEmergency
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Emergency Alert Sent!",
                style = MaterialTheme.typography.headlineMedium,
                color = OnEmergency
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = message,
                style = MaterialTheme.typography.bodyLarge,
                color = OnEmergency.copy(alpha = 0.9f)
            )
            Spacer(modifier = Modifier.height(24.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(
                        color = OnEmergency,
                        shape = RoundedCornerShape(8.dp)
                    )
                    .clickable(onClick = onDismiss)
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "OK",
                    style = MaterialTheme.typography.titleLarge,
                    color = Emergency
                )
            }
        }
    }
}
