package com.genvoice.caregiver.data.models

import com.google.gson.annotations.SerializedName

/**
 * Senior user data model
 */
data class Senior(
    @SerializedName("id")
    val id: String,

    @SerializedName("name")
    val name: String,

    @SerializedName("phone_number")
    val phoneNumber: String,

    @SerializedName("check_in_morning_time")
    val checkInMorningTime: String? = null,

    @SerializedName("check_in_evening_time")
    val checkInEveningTime: String? = null,

    @SerializedName("voice_speed")
    val voiceSpeed: Float? = 0.85f,

    @SerializedName("last_check_in")
    val lastCheckIn: String? = null,

    @SerializedName("is_active")
    val isActive: Boolean = true,

    @SerializedName("created_at")
    val createdAt: String? = null
)

/**
 * Dashboard data model (comprehensive senior overview)
 */
data class Dashboard(
    @SerializedName("senior")
    val senior: SeniorInfo,

    @SerializedName("wellness")
    val wellness: WellnessInfo,

    @SerializedName("check_ins")
    val checkIns: CheckInInfo,

    @SerializedName("medications")
    val medications: MedicationInfo,

    @SerializedName("emergencies")
    val emergencies: EmergencyInfo,

    @SerializedName("family_members")
    val familyMembers: List<FamilyMember>? = null
)

data class SeniorInfo(
    @SerializedName("name")
    val name: String,

    @SerializedName("phone")
    val phone: String
)

data class WellnessInfo(
    @SerializedName("overall_score")
    val overallScore: Float,

    @SerializedName("status")
    val status: String
)

data class CheckInInfo(
    @SerializedName("total_count")
    val totalCount: Int? = 0,

    @SerializedName("completion_rate")
    val completionRate: Float? = 0f,

    @SerializedName("last_check_in")
    val lastCheckIn: String? = null
)

data class MedicationInfo(
    @SerializedName("count")
    val count: Int,

    @SerializedName("active_count")
    val activeCount: Int? = 0,

    @SerializedName("compliance")
    val compliance: ComplianceInfo? = null
)

data class ComplianceInfo(
    @SerializedName("rate")
    val rate: Float,

    @SerializedName("taken")
    val taken: Int? = 0,

    @SerializedName("missed")
    val missed: Int? = 0
)

data class EmergencyInfo(
    @SerializedName("total_count")
    val totalCount: Int? = 0,

    @SerializedName("active_count")
    val activeCount: Int? = 0,

    @SerializedName("last_emergency")
    val lastEmergency: String? = null
)

data class FamilyMember(
    @SerializedName("id")
    val id: String,

    @SerializedName("name")
    val name: String,

    @SerializedName("relationship")
    val relationship: String,

    @SerializedName("phone_number")
    val phoneNumber: String,

    @SerializedName("is_primary")
    val isPrimary: Boolean = false
)
