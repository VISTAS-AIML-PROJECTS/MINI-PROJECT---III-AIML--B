package com.genvoice.caregiver.services

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import com.genvoice.caregiver.utils.Constants

/**
 * Schedules check-in notifications using AlarmManager
 */
object CheckInScheduler {

    private const val TAG = "CheckInScheduler"

    /**
     * Schedule a check-in notification
     *
     * @param context Application context
     * @param scheduleId Unique ID for this scheduled check-in
     * @param minutes Minutes from now to trigger notification
     * @param seniorName Name of senior (for personalization)
     */
    fun scheduleCheckIn(
        context: Context,
        scheduleId: String,
        minutes: Int,
        seniorName: String = Constants.DEMO_SENIOR_NAME
    ): Boolean {
        try {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

            // Create intent for alarm receiver
            val intent = Intent(context, CheckInAlarmReceiver::class.java).apply {
                putExtra(CheckInAlarmReceiver.EXTRA_SCHEDULE_ID, scheduleId)
                putExtra(CheckInAlarmReceiver.EXTRA_SENIOR_NAME, seniorName)
            }

            val pendingIntent = PendingIntent.getBroadcast(
                context,
                scheduleId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            // Calculate trigger time
            val triggerAtMillis = System.currentTimeMillis() + (minutes * 60 * 1000)

            // Schedule exact alarm
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                // Android 12+ requires SCHEDULE_EXACT_ALARM permission
                if (alarmManager.canScheduleExactAlarms()) {
                    alarmManager.setExactAndAllowWhileIdle(
                        AlarmManager.RTC_WAKEUP,
                        triggerAtMillis,
                        pendingIntent
                    )
                    Log.d(TAG, "Check-in scheduled for $minutes minutes from now (exact)")
                } else {
                    // Fallback to inexact alarm
                    alarmManager.setAndAllowWhileIdle(
                        AlarmManager.RTC_WAKEUP,
                        triggerAtMillis,
                        pendingIntent
                    )
                    Log.d(TAG, "Check-in scheduled for $minutes minutes from now (inexact)")
                }
            } else {
                // Pre-Android 12
                alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP,
                    triggerAtMillis,
                    pendingIntent
                )
                Log.d(TAG, "Check-in scheduled for $minutes minutes from now")
            }

            return true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to schedule check-in", e)
            return false
        }
    }

    /**
     * Cancel a scheduled check-in
     */
    fun cancelScheduledCheckIn(context: Context, scheduleId: String) {
        try {
            val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

            val intent = Intent(context, CheckInAlarmReceiver::class.java)
            val pendingIntent = PendingIntent.getBroadcast(
                context,
                scheduleId.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            alarmManager.cancel(pendingIntent)
            pendingIntent.cancel()

            Log.d(TAG, "Scheduled check-in cancelled: $scheduleId")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to cancel scheduled check-in", e)
        }
    }

    /**
     * Schedule daily check-ins (morning & evening)
     */
    fun scheduleDailyCheckIns(context: Context, seniorName: String = Constants.DEMO_SENIOR_NAME) {
        // Schedule morning check-in (8 AM)
        scheduleCheckIn(context, "daily_morning", calculateMinutesUntil(8, 0), seniorName)

        // Schedule evening check-in (7 PM)
        scheduleCheckIn(context, "daily_evening", calculateMinutesUntil(19, 0), seniorName)

        Log.d(TAG, "Daily check-ins scheduled")
    }

    /**
     * Calculate minutes until a specific hour:minute
     */
    private fun calculateMinutesUntil(targetHour: Int, targetMinute: Int): Int {
        val now = java.util.Calendar.getInstance()
        val target = java.util.Calendar.getInstance().apply {
            set(java.util.Calendar.HOUR_OF_DAY, targetHour)
            set(java.util.Calendar.MINUTE, targetMinute)
            set(java.util.Calendar.SECOND, 0)

            // If target time has passed today, schedule for tomorrow
            if (before(now)) {
                add(java.util.Calendar.DAY_OF_MONTH, 1)
            }
        }

        val diffMillis = target.timeInMillis - now.timeInMillis
        return (diffMillis / (60 * 1000)).toInt()
    }
}
