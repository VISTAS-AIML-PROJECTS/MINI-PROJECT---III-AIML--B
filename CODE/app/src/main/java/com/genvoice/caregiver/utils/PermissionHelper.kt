package com.genvoice.caregiver.utils

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

/**
 * Helper for handling runtime permissions
 */
object PermissionHelper {

    /**
     * Permission request codes
     */
    const val PERMISSION_REQUEST_CODE = 1001
    const val PERMISSION_SETTINGS_REQUEST_CODE = 1002

    /**
     * Required permissions
     */
    val REQUIRED_PERMISSIONS = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.POST_NOTIFICATIONS
        )
    } else {
        arrayOf(
            Manifest.permission.RECORD_AUDIO
        )
    }

    /**
     * Check if all required permissions are granted
     */
    fun hasAllPermissions(context: Context): Boolean {
        return REQUIRED_PERMISSIONS.all { permission ->
            ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
        }
    }

    /**
     * Check if a specific permission is granted
     */
    fun hasPermission(context: Context, permission: String): Boolean {
        return ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
    }

    /**
     * Check if microphone permission is granted
     */
    fun hasMicrophonePermission(context: Context): Boolean {
        return hasPermission(context, Manifest.permission.RECORD_AUDIO)
    }

    /**
     * Check if notification permission is granted (Android 13+)
     */
    fun hasNotificationPermission(context: Context): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            hasPermission(context, Manifest.permission.POST_NOTIFICATIONS)
        } else {
            true // Not required before Android 13
        }
    }

    /**
     * Request all required permissions
     */
    fun requestPermissions(activity: Activity) {
        ActivityCompat.requestPermissions(
            activity,
            REQUIRED_PERMISSIONS,
            PERMISSION_REQUEST_CODE
        )
    }

    /**
     * Request specific permission
     */
    fun requestPermission(activity: Activity, permission: String) {
        ActivityCompat.requestPermissions(
            activity,
            arrayOf(permission),
            PERMISSION_REQUEST_CODE
        )
    }

    /**
     * Check if we should show permission rationale
     */
    fun shouldShowRationale(activity: Activity, permission: String): Boolean {
        return ActivityCompat.shouldShowRequestPermissionRationale(activity, permission)
    }

    /**
     * Get list of denied permissions
     */
    fun getDeniedPermissions(context: Context): List<String> {
        return REQUIRED_PERMISSIONS.filter { permission ->
            ContextCompat.checkSelfPermission(context, permission) != PackageManager.PERMISSION_GRANTED
        }
    }

    /**
     * Handle permission request result
     * Returns true if all permissions granted, false otherwise
     */
    fun onPermissionResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ): Boolean {
        if (requestCode != PERMISSION_REQUEST_CODE) return false

        return grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }
    }

    /**
     * Open app settings to manually grant permissions
     */
    fun openAppSettings(context: Context) {
        val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
            data = Uri.fromParts("package", context.packageName, null)
        }
        context.startActivity(intent)
    }

    /**
     * Get user-friendly permission name
     */
    fun getPermissionName(permission: String): String {
        return when (permission) {
            Manifest.permission.RECORD_AUDIO -> "Microphone"
            Manifest.permission.POST_NOTIFICATIONS -> "Notifications"
            else -> permission.substringAfterLast(".")
        }
    }

    /**
     * Get permission rationale message
     */
    fun getPermissionRationale(permission: String): String {
        return when (permission) {
            Manifest.permission.RECORD_AUDIO ->
                "GenVoice needs microphone permission to hear you and have conversations. This is essential for the app to work."
            Manifest.permission.POST_NOTIFICATIONS ->
                "GenVoice needs notification permission to remind you about check-ins and medications."
            else -> "GenVoice needs this permission to work properly."
        }
    }

    /**
     * Get all missing permissions with rationales
     */
    fun getMissingPermissionsInfo(context: Context): List<PermissionInfo> {
        return getDeniedPermissions(context).map { permission ->
            PermissionInfo(
                permission = permission,
                name = getPermissionName(permission),
                rationale = getPermissionRationale(permission)
            )
        }
    }
}

/**
 * Permission information data class
 */
data class PermissionInfo(
    val permission: String,
    val name: String,
    val rationale: String
)
