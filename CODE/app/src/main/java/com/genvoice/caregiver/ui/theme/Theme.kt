package com.genvoice.caregiver.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

/**
 * Premium Dark color scheme for GenVoice
 * Elite royal theme: Black, Gold, White
 * High contrast for elderly users
 */
private val DarkColorScheme = darkColorScheme(
    primary = Primary,              // Royal Gold
    onPrimary = OnPrimary,          // Black on gold
    primaryContainer = PrimaryDark,
    onPrimaryContainer = PrimaryLight,

    secondary = Secondary,          // Elegant White
    onSecondary = OnSecondary,      // Black on white
    secondaryContainer = SecondaryDark,
    onSecondaryContainer = SecondaryLight,

    error = Emergency,              // Vibrant Red
    onError = OnEmergency,          // White on red
    errorContainer = EmergencyDark,
    onErrorContainer = EmergencyLight,

    background = Background,        // Deep Black
    onBackground = OnBackground,    // White text

    surface = Surface,              // Card Black
    onSurface = OnSurface,          // White text

    surfaceVariant = CardBackground,
    onSurfaceVariant = TextSecondary,

    outline = DividerColor,
    outlineVariant = DividerColor
)

/**
 * GenVoice Premium Dark Theme
 * - Elite royal colors: Black, Gold, White
 * - High contrast for elderly
 * - Professional luxury feel
 * - Large text sizes
 * - Clean, premium design
 */
@Composable
fun GenVoiceTheme(
    darkTheme: Boolean = true,  // Always dark - premium theme
    content: @Composable () -> Unit
) {
    val colorScheme = DarkColorScheme  // Premium dark mode

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = Background.toArgb()  // Black status bar
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
