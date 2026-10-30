package com.genvoice.caregiver.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.genvoice.caregiver.ui.theme.*

/**
 * Status card to display wellness, check-in, or medication status
 */
@Composable
fun StatusCard(
    title: String,
    value: String,
    icon: ImageVector,
    statusColor: Color = Primary,
    modifier: Modifier = Modifier,
    subtitle: String? = null
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = CardBackground
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = 4.dp
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Icon with colored background
            Box(
                modifier = Modifier
                    .size(60.dp)
                    .background(
                        color = statusColor.copy(alpha = 0.2f),
                        shape = RoundedCornerShape(12.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = title,
                    modifier = Modifier.size(32.dp),
                    tint = statusColor
                )
            }

            Spacer(modifier = Modifier.width(16.dp))

            // Content
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    color = TextSecondary
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = value,
                    style = MaterialTheme.typography.headlineSmall,
                    color = OnBackground
                )
                if (subtitle != null) {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = subtitle,
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondary
                    )
                }
            }
        }
    }
}

/**
 * Wellness status card with color-coded wellness level
 */
@Composable
fun WellnessStatusCard(
    wellnessScore: Float,
    wellnessStatus: String,
    modifier: Modifier = Modifier
) {
    val (color, statusText) = when (wellnessStatus.lowercase()) {
        "good" -> Pair(WellnessGood, "Feeling Good")
        "fair" -> Pair(WellnessFair, "Doing Okay")
        "poor" -> Pair(WellnessPoor, "Needs Attention")
        else -> Pair(Primary, wellnessStatus)
    }

    StatusCard(
        title = "Wellness",
        value = "$wellnessScore/100",
        subtitle = statusText,
        icon = Icons.Filled.Favorite,
        statusColor = color,
        modifier = modifier
    )
}

/**
 * Check-in completion card
 */
@Composable
fun CheckInStatusCard(
    completionRate: Float,
    lastCheckIn: String?,
    modifier: Modifier = Modifier
) {
    val color = when {
        completionRate >= 90f -> WellnessGood
        completionRate >= 70f -> WellnessFair
        else -> WellnessPoor
    }

    StatusCard(
        title = "Check-Ins",
        value = "${completionRate.toInt()}%",
        subtitle = lastCheckIn ?: "No recent check-ins",
        icon = Icons.Filled.CheckCircle,
        statusColor = color,
        modifier = modifier
    )
}

/**
 * Medication compliance card
 */
@Composable
fun MedicationStatusCard(
    complianceRate: Float,
    medicationCount: Int,
    modifier: Modifier = Modifier
) {
    val color = when {
        complianceRate >= 95f -> WellnessGood
        complianceRate >= 80f -> WellnessFair
        else -> WellnessPoor
    }

    StatusCard(
        title = "Medications",
        value = "${complianceRate.toInt()}%",
        subtitle = "$medicationCount active medications",
        icon = Icons.Filled.Medication,
        statusColor = color,
        modifier = modifier
    )
}

/**
 * Simple info card
 */
@Composable
fun InfoCard(
    message: String,
    modifier: Modifier = Modifier,
    icon: ImageVector = Icons.Filled.Info,
    color: Color = Primary
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(32.dp)
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                text = message,
                style = MaterialTheme.typography.bodyLarge,
                color = OnBackground
            )
        }
    }
}
