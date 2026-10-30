package com.genvoice.caregiver.services

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.genvoice.caregiver.MainActivity
import com.genvoice.caregiver.R
import com.genvoice.caregiver.utils.Constants

/**
 * Receives alarm broadcasts and shows check-in notifications
 */
class CheckInAlarmReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val scheduleId = intent.getStringExtra(EXTRA_SCHEDULE_ID)
        val seniorName = intent.getStringExtra(EXTRA_SENIOR_NAME) ?: "there"

        // Show notification
        showCheckInNotification(context, scheduleId, seniorName)
    }

    private fun showCheckInNotification(context: Context, scheduleId: String?, seniorName: String) {
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Create notification channel (Android 8.0+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                Constants.NotificationChannels.CHECKIN_CHANNEL_ID,
                "Check-In Reminders",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Reminders for daily check-ins"
                enableVibration(true)
                setShowBadge(true)
            }
            notificationManager.createNotificationChannel(channel)
        }

        // Intent to open app and start check-in
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("START_CHECKIN", true)
            putExtra("SCHEDULE_ID", scheduleId)
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            scheduleId?.hashCode() ?: Constants.NotificationIds.CHECKIN_REMINDER,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Build notification
        val notification = NotificationCompat.Builder(context, Constants.NotificationChannels.CHECKIN_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Time for your check-in!")
            .setContentText("Hi $seniorName! Let's do a quick check-in.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_REMINDER)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setVibrate(longArrayOf(0, 500, 200, 500))
            .build()

        // Show notification
        notificationManager.notify(
            scheduleId?.hashCode() ?: Constants.NotificationIds.CHECKIN_REMINDER,
            notification
        )
    }

    companion object {
        const val EXTRA_SCHEDULE_ID = "schedule_id"
        const val EXTRA_SENIOR_NAME = "senior_name"
    }
}
