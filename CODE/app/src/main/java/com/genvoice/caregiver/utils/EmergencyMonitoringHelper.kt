package com.genvoice.caregiver.utils

import android.content.Context
import android.content.Intent
import android.os.Build
import com.genvoice.caregiver.services.EmergencyPollingService

/**
 * Helper class to manage emergency monitoring service
 */
object EmergencyMonitoringHelper {

    /**
     * Start emergency monitoring for a senior
     */
    fun startMonitoring(context: Context, seniorId: String) {
        val intent = Intent(context, EmergencyPollingService::class.java).apply {
            action = EmergencyPollingService.ACTION_START_POLLING
            putExtra(EmergencyPollingService.EXTRA_SENIOR_ID, seniorId)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(intent)
        } else {
            context.startService(intent)
        }
    }

    /**
     * Stop emergency monitoring
     */
    fun stopMonitoring(context: Context) {
        val intent = Intent(context, EmergencyPollingService::class.java).apply {
            action = EmergencyPollingService.ACTION_STOP_POLLING
        }
        context.startService(intent)
    }

    /**
     * Check if monitoring is enabled in preferences
     */
    fun isMonitoringEnabled(context: Context): Boolean {
        val prefs = context.getSharedPreferences(Constants.PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean("emergency_monitoring_enabled", true) // Default: enabled
    }

    /**
     * Enable/disable monitoring in preferences
     */
    fun setMonitoringEnabled(context: Context, enabled: Boolean) {
        val prefs = context.getSharedPreferences(Constants.PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putBoolean("emergency_monitoring_enabled", enabled).apply()
    }
}
