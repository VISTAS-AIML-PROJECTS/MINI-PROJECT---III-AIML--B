package com.genvoice.caregiver.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.media.RingtoneManager
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.genvoice.caregiver.MainActivity
import com.genvoice.caregiver.R
import com.genvoice.caregiver.data.api.GenVoiceApi
import com.genvoice.caregiver.utils.Constants
import kotlinx.coroutines.*
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

/**
 * Background service that polls backend for emergency alerts
 * Runs every 30 seconds to check for new emergencies
 */
class EmergencyPollingService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var pollingJob: Job? = null

    private lateinit var api: GenVoiceApi
    private var lastCheckedTimestamp: String = ""

    companion object {
        const val ACTION_START_POLLING = "com.genvoice.caregiver.START_POLLING"
        const val ACTION_STOP_POLLING = "com.genvoice.caregiver.STOP_POLLING"
        const val EXTRA_SENIOR_ID = "senior_id"

        private const val POLLING_INTERVAL_MS = 30000L // 30 seconds
        private const val FOREGROUND_NOTIFICATION_ID = 1001
        private const val EMERGENCY_NOTIFICATION_ID_BASE = 2000
    }

    override fun onCreate() {
        super.onCreate()

        // Initialize API client
        val retrofit = Retrofit.Builder()
            .baseUrl(Constants.API_BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(GenVoiceApi::class.java)

        // Start as foreground service
        startForeground(FOREGROUND_NOTIFICATION_ID, createForegroundNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START_POLLING -> {
                val seniorId = intent.getStringExtra(EXTRA_SENIOR_ID)
                if (seniorId != null) {
                    startPolling(seniorId)
                }
            }
            ACTION_STOP_POLLING -> {
                stopPolling()
                stopSelf()
            }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    /**
     * Start polling for emergencies
     */
    private fun startPolling(seniorId: String) {
        // Cancel existing job if any
        pollingJob?.cancel()

        // Initialize last checked timestamp to now
        if (lastCheckedTimestamp.isEmpty()) {
            lastCheckedTimestamp = getCurrentTimestamp()
        }

        pollingJob = serviceScope.launch {
            while (isActive) {
                try {
                    checkForEmergencies(seniorId)
                } catch (e: Exception) {
                    // Log error but continue polling
                    println("Emergency polling error: ${e.message}")
                }

                // Wait 30 seconds before next check
                delay(POLLING_INTERVAL_MS)
            }
        }
    }

    /**
     * Stop polling
     */
    private fun stopPolling() {
        pollingJob?.cancel()
        pollingJob = null
    }

    /**
     * Check backend for new emergencies
     */
    private suspend fun checkForEmergencies(seniorId: String) {
        try {
            val response = api.getEmergencies(seniorId)

            if (response.isSuccessful) {
                val emergencies = response.body()?.data ?: emptyList()

                // Filter for new emergencies (after last checked timestamp)
                val newEmergencies = emergencies.filter { emergency ->
                    emergency.triggeredAt > lastCheckedTimestamp &&
                    emergency.status == "active"
                }

                // Show notification for each new emergency
                newEmergencies.forEach { emergency ->
                    showEmergencyNotification(emergency)
                }

                // Update last checked timestamp
                if (newEmergencies.isNotEmpty()) {
                    lastCheckedTimestamp = newEmergencies.first().triggeredAt
                }
            }
        } catch (e: Exception) {
            println("Error checking emergencies: ${e.message}")
        }
    }

    /**
     * Show emergency notification
     */
    private fun showEmergencyNotification(emergency: com.genvoice.caregiver.data.models.Emergency) {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Create notification channel for Android O+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                Constants.NotificationChannels.EMERGENCY_ALERTS_CHANNEL_ID,
                "Emergency Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Critical emergency alerts"
                enableVibration(true)
                enableLights(true)
                setShowBadge(true)
            }
            notificationManager.createNotificationChannel(channel)
        }

        // Create intent to open app
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("open_emergency", true)
            putExtra("emergency_id", emergency.id)
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            emergency.id.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Determine notification text based on alert type
        val title = when (emergency.alertType) {
            "manual" -> "🚨 EMERGENCY ALERT"
            "keyword" -> "⚠️ URGENT: Emergency Detected"
            "fall_detection" -> "⚠️ FALL DETECTED"
            "missed_checkin" -> "⚠️ Missed Check-In"
            else -> "🚨 ALERT"
        }

        val message = emergency.description ?: "Immediate attention needed. Please check on your loved one."

        // Get default alarm sound
        val alarmSound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)

        // Build notification
        val notification = NotificationCompat.Builder(this, Constants.NotificationChannels.EMERGENCY_ALERTS_CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setColor(0xFFD32F2F.toInt()) // Red color
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(true)
            .setSound(alarmSound)
            .setVibrate(longArrayOf(0, 500, 200, 500, 200, 500)) // Vibration pattern
            .setContentIntent(pendingIntent)
            .build()

        // Show notification with unique ID
        val notificationId = EMERGENCY_NOTIFICATION_ID_BASE + emergency.id.hashCode()
        notificationManager.notify(notificationId, notification)
    }

    /**
     * Create foreground service notification
     */
    private fun createForegroundNotification(): Notification {
        // Create notification channel for Android O+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                Constants.NotificationChannels.EMERGENCY_SERVICE_CHANNEL_ID,
                "Emergency Monitoring",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Monitors for emergency alerts"
                setShowBadge(false)
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager?.createNotificationChannel(channel)
        }

        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, Constants.NotificationChannels.EMERGENCY_SERVICE_CHANNEL_ID)
            .setContentTitle("GenVoice Monitoring")
            .setContentText("Watching for emergency alerts")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setShowWhen(false)
            .build()
    }

    /**
     * Get current timestamp in ISO format
     */
    private fun getCurrentTimestamp(): String {
        return java.time.Instant.now().toString()
    }

    override fun onDestroy() {
        super.onDestroy()
        stopPolling()
        serviceScope.cancel()
    }
}
