package com.genvoice.caregiver.utils

import java.text.SimpleDateFormat
import java.util.*

/**
 * Utility functions for date and time operations
 */
object DateTimeUtils {

    /**
     * Format patterns
     */
    private const val ISO_8601_FORMAT = "yyyy-MM-dd'T'HH:mm:ss'Z'"
    private const val DISPLAY_DATE_FORMAT = "MMMM dd, yyyy"
    private const val DISPLAY_TIME_FORMAT = "h:mm a"
    private const val DISPLAY_DATETIME_FORMAT = "MMM dd, yyyy h:mm a"

    /**
     * Get current timestamp in ISO 8601 format for API
     */
    fun getCurrentIso8601Timestamp(): String {
        val sdf = SimpleDateFormat(ISO_8601_FORMAT, Locale.US)
        sdf.timeZone = TimeZone.getTimeZone("UTC")
        return sdf.format(Date())
    }

    /**
     * Format timestamp for display
     */
    fun formatForDisplay(timestamp: String): String {
        return try {
            val inputFormat = SimpleDateFormat(ISO_8601_FORMAT, Locale.US)
            inputFormat.timeZone = TimeZone.getTimeZone("UTC")
            val date = inputFormat.parse(timestamp) ?: return timestamp

            val outputFormat = SimpleDateFormat(DISPLAY_DATETIME_FORMAT, Locale.US)
            outputFormat.timeZone = TimeZone.getDefault()
            outputFormat.format(date)
        } catch (e: Exception) {
            timestamp
        }
    }

    /**
     * Get current hour (0-23)
     */
    fun getCurrentHour(): Int {
        return Calendar.getInstance().get(Calendar.HOUR_OF_DAY)
    }

    /**
     * Check if it's morning (6 AM - 12 PM)
     */
    fun isMorning(): Boolean {
        val hour = getCurrentHour()
        return hour in 6..11
    }

    /**
     * Check if it's afternoon (12 PM - 6 PM)
     */
    fun isAfternoon(): Boolean {
        val hour = getCurrentHour()
        return hour in 12..17
    }

    /**
     * Check if it's evening (6 PM - 12 AM)
     */
    fun isEvening(): Boolean {
        val hour = getCurrentHour()
        return hour in 18..23
    }

    /**
     * Check if it's night (12 AM - 6 AM)
     */
    fun isNight(): Boolean {
        val hour = getCurrentHour()
        return hour in 0..5
    }

    /**
     * Get greeting based on time of day
     * FIXED: Use generic alternating greetings instead of time-based
     */
    fun getGreeting(): String {
        // Rotate through different friendly greetings
        val greetings = listOf(
            "Hi",
            "Hello",
            "Welcome back",
            "Hey there"
        )

        // Use current hour to pick greeting (changes throughout the day)
        val index = getCurrentHour() % greetings.size
        return greetings[index]
    }

    /**
     * Get time-appropriate check-in type
     */
    fun getCurrentCheckInType(): String {
        val hour = getCurrentHour()
        return when {
            hour in 6..14 -> Constants.CheckInType.MORNING
            hour in 15..23 -> Constants.CheckInType.EVENING
            else -> Constants.CheckInType.EVENING // Default to evening for late night
        }
    }

    /**
     * Format time for display (e.g., "8:00 AM")
     */
    fun formatTime(hour: Int, minute: Int): String {
        val calendar = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, hour)
            set(Calendar.MINUTE, minute)
        }
        val sdf = SimpleDateFormat(DISPLAY_TIME_FORMAT, Locale.US)
        return sdf.format(calendar.time)
    }

    /**
     * Check if current time is past a specific time today
     */
    fun isTimePast(hour: Int, minute: Int): Boolean {
        val now = Calendar.getInstance()
        val target = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, hour)
            set(Calendar.MINUTE, minute)
            set(Calendar.SECOND, 0)
        }
        return now.after(target)
    }

    /**
     * Get time until next check-in in minutes
     */
    fun getMinutesUntilNextCheckIn(hour: Int, minute: Int): Int {
        val now = Calendar.getInstance()
        val target = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, hour)
            set(Calendar.MINUTE, minute)
            set(Calendar.SECOND, 0)

            // If time has passed today, schedule for tomorrow
            if (before(now)) {
                add(Calendar.DAY_OF_MONTH, 1)
            }
        }

        val diffMs = target.timeInMillis - now.timeInMillis
        return (diffMs / (60 * 1000)).toInt()
    }

    /**
     * Convert milliseconds to human-readable duration
     */
    fun formatDuration(milliseconds: Long): String {
        val seconds = milliseconds / 1000
        val minutes = seconds / 60
        val hours = minutes / 60

        return when {
            hours > 0 -> "${hours}h ${minutes % 60}m"
            minutes > 0 -> "${minutes}m"
            else -> "${seconds}s"
        }
    }

    /**
     * Get relative time string (e.g., "5 minutes ago", "2 hours ago")
     */
    fun getRelativeTimeString(timestamp: String): String {
        return try {
            val inputFormat = SimpleDateFormat(ISO_8601_FORMAT, Locale.US)
            inputFormat.timeZone = TimeZone.getTimeZone("UTC")
            val date = inputFormat.parse(timestamp) ?: return timestamp

            val now = Date()
            val diffMs = now.time - date.time
            val diffSeconds = diffMs / 1000
            val diffMinutes = diffSeconds / 60
            val diffHours = diffMinutes / 60
            val diffDays = diffHours / 24

            when {
                diffMinutes < 1 -> "Just now"
                diffMinutes < 60 -> "$diffMinutes minute${if (diffMinutes != 1L) "s" else ""} ago"
                diffHours < 24 -> "$diffHours hour${if (diffHours != 1L) "s" else ""} ago"
                diffDays < 7 -> "$diffDays day${if (diffDays != 1L) "s" else ""} ago"
                else -> formatForDisplay(timestamp)
            }
        } catch (e: Exception) {
            timestamp
        }
    }
}
