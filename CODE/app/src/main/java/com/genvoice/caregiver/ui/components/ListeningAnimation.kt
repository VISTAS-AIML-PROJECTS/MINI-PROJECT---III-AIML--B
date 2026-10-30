package com.genvoice.caregiver.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.genvoice.caregiver.ui.theme.Listening
import kotlin.math.sin

/**
 * Listening animation with sound wave effect
 * Shows visual feedback while the app is listening
 */
@Composable
fun ListeningAnimation(
    modifier: Modifier = Modifier,
    message: String = "I'm listening..."
) {
    // Animated wave effect
    val infiniteTransition = rememberInfiniteTransition(label = "wave")
    val phase by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "phase"
    )

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Wave visualization
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(100.dp)
                .padding(horizontal = 32.dp)
        ) {
            val barCount = 20
            val barWidth = size.width / barCount
            val centerY = size.height / 2

            repeat(barCount) { index ->
                val x = index * barWidth + barWidth / 2
                val amplitude = size.height / 4
                val frequency = 0.5f
                val offset = (phase + index * 18f) * Math.PI.toFloat() / 180f
                val height = amplitude * sin(frequency * offset) + amplitude

                drawLine(
                    color = Listening,
                    start = Offset(x, centerY - height / 2),
                    end = Offset(x, centerY + height / 2),
                    strokeWidth = barWidth * 0.6f
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Message text
        Text(
            text = message,
            style = MaterialTheme.typography.titleLarge,
            color = Listening
        )
    }
}

/**
 * Simple pulsing circle animation
 */
@Composable
fun PulsingCircle(
    color: Color = Listening,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val scale by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    Canvas(
        modifier = modifier.size(80.dp)
    ) {
        drawCircle(
            color = color,
            radius = size.minDimension / 2 * scale,
            alpha = 0.3f
        )
        drawCircle(
            color = color,
            radius = size.minDimension / 3,
            alpha = 1f
        )
    }
}
