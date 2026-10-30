package com.genvoice.caregiver

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.genvoice.caregiver.ui.screens.DashboardScreen
import com.genvoice.caregiver.ui.theme.GenVoiceTheme
import com.genvoice.caregiver.utils.Constants
import com.genvoice.caregiver.utils.EmergencyMonitoringHelper

/**
 * Main Activity - Caregiver Dashboard
 * Shows recent check-ins and conversations with seniors
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Start emergency monitoring service
        startEmergencyMonitoring()

        setContent {
            GenVoiceTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    DashboardScreen()
                }
            }
        }
    }

    /**
     * Start emergency monitoring for the demo senior
     * In production, this would monitor all seniors assigned to this caregiver
     */
    private fun startEmergencyMonitoring() {
        if (EmergencyMonitoringHelper.isMonitoringEnabled(this)) {
            EmergencyMonitoringHelper.startMonitoring(this, Constants.DEMO_SENIOR_ID)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        // Note: Service continues running in background even when app is closed
        // This is intentional for emergency monitoring
    }
}
