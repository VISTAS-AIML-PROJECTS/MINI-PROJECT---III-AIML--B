package com.genvoice.caregiver.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.genvoice.caregiver.services.VoiceState
import com.genvoice.caregiver.ui.theme.*

/**
 * Big voice button for elderly users
 * Large, easy to tap, with clear visual feedback
 */
@Composable
fun BigVoiceButton(
    voiceState: VoiceState,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    // Animation for listening state
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    // Get button color and text based on state
    val (backgroundColor, textColor, buttonText, iconTint) = when (voiceState) {
        VoiceState.LISTENING -> {
            Tuple4(Listening, Color.White, "Listening...", Color.White)
        }
        VoiceState.SPEAKING -> {
            Tuple4(Speaking, Color.White, "Speaking...", Color.White)
        }
        VoiceState.PROCESSING -> {
            Tuple4(Primary, Color.White, "Processing...", Color.White)
        }
        VoiceState.ERROR -> {
            Tuple4(Error, Color.White, "Try Again", Color.White)
        }
        else -> {
            Tuple4(Primary, Color.White, "Talk to GenVoice", Color.White)
        }
    }

    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Big circular button
        Box(
            modifier = Modifier
                .size(if (voiceState == VoiceState.LISTENING) 200.dp else 180.dp)
                .scale(if (voiceState == VoiceState.LISTENING) scale else 1f)
                .clip(CircleShape)
                .background(if (enabled) backgroundColor else TextDisabled)
                .clickable(
                    enabled = enabled,
                    onClick = onClick,
                    indication = null,
                    interactionSource = remember { MutableInteractionSource() }
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Filled.Mic,
                contentDescription = "Microphone",
                modifier = Modifier.size(80.dp),
                tint = iconTint
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Button text
        Text(
            text = buttonText,
            style = MaterialTheme.typography.headlineSmall,
            color = if (enabled) OnBackground else TextDisabled
        )
    }
}

/**
 * Helper data class for button state
 */
private data class Tuple4<A, B, C, D>(
    val first: A,
    val second: B,
    val third: C,
    val fourth: D
)
