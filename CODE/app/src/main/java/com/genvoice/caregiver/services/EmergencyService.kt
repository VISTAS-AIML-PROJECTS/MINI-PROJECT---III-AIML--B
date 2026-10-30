package com.genvoice.caregiver.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.genvoice.caregiver.MainActivity
import com.genvoice.caregiver.R
import com.genvoice.caregiver.utils.Constants

/**
 * Foreground service for emergency detection
 * Runs in background to detect emergency keywords in voice
 *
 * NOTE: This is a placeholder implementation.
 * Full implementation would require continuous voice monitoring
 * which is battery-intensive and requires careful implementation.
 */
class EmergencyService : Service() {

    companion object {
        const val ACTION_START = "com.genvoice.senior.action.START_EMERGENCY_SERVICE"
        const val ACTION_STOP = "com.genvoice.senior.action.STOP_EMERGENCY_SERVICE"
    }

    override fun onCreate() {
        super.onCreate()
        startForeground(
            Constants.NotificationIds.EMERGENCY_SERVICE,
            createNotification()
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                // Start emergency monitoring
                // This would initialize voice monitoring in production
            }
            ACTION_STOP -> {
                stopSelf()
            }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    /**
     * Create foreground service notification
     */
    private fun createNotification(): Notification {
        // Create notification channel for Android O+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                Constants.NotificationChannels.EMERGENCY_CHANNEL_ID,
                "Emergency Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Emergency detection service"
                setShowBadge(false)
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager?.createNotificationChannel(channel)
        }

        // Create intent to open app when notification is tapped
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, Constants.NotificationChannels.EMERGENCY_CHANNEL_ID)
            .setContentTitle("GenVoice Emergency Service")
            .setContentText("Monitoring for emergency keywords")
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    override fun onDestroy() {
        super.onDestroy()
        // Clean up resources
    }
}
