package com.genvoice.caregiver

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import com.genvoice.caregiver.utils.Constants

/**
 * GenVoice Application class
 * Initializes app-wide components
 */
class GenVoiceApplication : Application() {

    override fun onCreate() {
        super.onCreate()

        // Create notification channels
        createNotificationChannels()
    }

    /**
     * Create notification channels for medications, check-ins, and emergency service
     */
    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationManager = getSystemService(NotificationManager::class.java)

            // Medication reminder channel
            val medicationChannel = NotificationChannel(
                Constants.NotificationChannels.MEDICATION_CHANNEL_ID,
                "Medication Reminders",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notifications for medication reminders"
                enableVibration(true)
                enableLights(true)
            }

            // Check-in reminder channel
            val checkInChannel = NotificationChannel(
                Constants.NotificationChannels.CHECKIN_CHANNEL_ID,
                "Check-In Reminders",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Notifications for daily check-in reminders"
                enableVibration(true)
            }

            // Emergency service channel
            val emergencyChannel = NotificationChannel(
                Constants.NotificationChannels.EMERGENCY_CHANNEL_ID,
                "Emergency Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Emergency detection service notification"
                setShowBadge(false)
            }

            // Register channels
            notificationManager?.createNotificationChannel(medicationChannel)
            notificationManager?.createNotificationChannel(checkInChannel)
            notificationManager?.createNotificationChannel(emergencyChannel)
        }
    }
}
