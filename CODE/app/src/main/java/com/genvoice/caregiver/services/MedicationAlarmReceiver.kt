package com.genvoice.caregiver.services

import android.app.AlarmManager
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
import java.util.Calendar

/**
 * BroadcastReceiver for medication alarm notifications
 * Triggers at scheduled medication times
 */
class MedicationAlarmReceiver : BroadcastReceiver() {

    companion object {
        private const val EXTRA_MEDICATION_ID = "medication_id"
        private const val EXTRA_MEDICATION_NAME = "medication_name"

        /**
         * Schedule medication alarm
         */
        fun scheduleMedicationAlarm(
            context: Context,
            medicationId: String,
            medicationName: String,
            hour: Int,
            minute: Int
        ) {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val intent = Intent(context, MedicationAlarmReceiver::class.java).apply {
                putExtra(EXTRA_MEDICATION_ID, medicationId)
                putExtra(EXTRA_MEDICATION_NAME, medicationName)
            }

            val pendingIntent = PendingIntent.getBroadcast(
                context,
                medicationId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            // Set alarm time
            val calendar = Calendar.getInstance().apply {
                set(Calendar.HOUR_OF_DAY, hour)
                set(Calendar.MINUTE, minute)
                set(Calendar.SECOND, 0)

                // If time has passed today, schedule for tomorrow
                if (before(Calendar.getInstance())) {
                    add(Calendar.DAY_OF_MONTH, 1)
                }
            }

            // Schedule repeating alarm
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP,
                    calendar.timeInMillis,
                    pendingIntent
                )
            } else {
                alarmManager.setExact(
                    AlarmManager.RTC_WAKEUP,
                    calendar.timeInMillis,
                    pendingIntent
                )
            }
        }

        /**
         * Cancel medication alarm
         */
        fun cancelMedicationAlarm(
            context: Context,
            medicationId: String
        ) {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
            val intent = Intent(context, MedicationAlarmReceiver::class.java)
            val pendingIntent = PendingIntent.getBroadcast(
                context,
                medicationId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            alarmManager.cancel(pendingIntent)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        val medicationId = intent.getStringExtra(EXTRA_MEDICATION_ID) ?: return
        val medicationName = intent.getStringExtra(EXTRA_MEDICATION_NAME) ?: "your medication"

        // Show notification
        showMedicationNotification(context, medicationId, medicationName)

        // Reschedule for next day
        // In production, this would check the medication schedule and reschedule accordingly
    }

    /**
     * Show medication reminder notification
     */
    private fun showMedicationNotification(
        context: Context,
        medicationId: String,
        medicationName: String
    ) {
        val notificationManager =
            context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Create intent to open app
        val intent = Intent(context, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )

        // Build notification
        val notification = NotificationCompat.Builder(
            context,
            Constants.NotificationChannels.MEDICATION_CHANNEL_ID
        )
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Time for Medication")
            .setContentText("It's time to take your $medicationName")
            .setStyle(
                NotificationCompat.BigTextStyle()
                    .bigText("It's time to take your $medicationName. Don't forget!")
            )
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setVibrate(longArrayOf(0, 500, 200, 500))
            .build()

        // Show notification
        notificationManager.notify(
            medicationId.hashCode(),
            notification
        )
    }
}
