package com.genvoice.caregiver.viewmodels

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.genvoice.caregiver.data.api.Result
import com.genvoice.caregiver.data.models.Medication
import com.genvoice.caregiver.data.models.MedicationCompliance
import com.genvoice.caregiver.data.models.MedicationTakenResponse
import com.genvoice.caregiver.data.repository.MedicationRepository
import com.genvoice.caregiver.utils.Constants
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for medication operations
 */
class MedicationViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = MedicationRepository()

    // Medications list
    private val _medications = MutableStateFlow<List<Medication>>(emptyList())
    val medications: StateFlow<List<Medication>> = _medications.asStateFlow()

    // Current medication being taken
    private val _currentMedication = MutableStateFlow<Medication?>(null)
    val currentMedication: StateFlow<Medication?> = _currentMedication.asStateFlow()

    // Medication taken result
    private val _medicationTaken = MutableStateFlow<MedicationTakenResponse?>(null)
    val medicationTaken: StateFlow<MedicationTakenResponse?> = _medicationTaken.asStateFlow()

    // Compliance data
    private val _compliance = MutableStateFlow<MedicationCompliance?>(null)
    val compliance: StateFlow<MedicationCompliance?> = _compliance.asStateFlow()

    // Due medications
    private val _dueMedications = MutableStateFlow<List<Medication>>(emptyList())
    val dueMedications: StateFlow<List<Medication>> = _dueMedications.asStateFlow()

    // Loading and error states
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    init {
        loadMedications()
    }

    /**
     * Load medications for the senior
     */
    fun loadMedications() {
        viewModelScope.launch {
            _isLoading.value = true
            when (val result = repository.getMedications(Constants.DEMO_SENIOR_ID)) {
                is Result.Success -> {
                    _medications.value = result.data
                    checkDueMedications(result.data)
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
            _isLoading.value = false
        }
    }

    /**
     * Check which medications are due now
     */
    private fun checkDueMedications(medications: List<Medication>) {
        val due = medications.filter { repository.isMedicationDue(it) }
        _dueMedications.value = due
    }

    /**
     * Log medication as taken
     */
    fun logMedicationTaken(medication: Medication, notes: String? = null) {
        viewModelScope.launch {
            _isLoading.value = true
            _currentMedication.value = medication

            when (val result = repository.logMedicationTaken(
                medicationId = medication.id,
                seniorId = Constants.DEMO_SENIOR_ID,
                notes = notes
            )) {
                is Result.Success -> {
                    _medicationTaken.value = result.data
                    // Reload medications to update due list
                    loadMedications()
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
            _isLoading.value = false
        }
    }

    /**
     * Log medication taken by ID (for hardcoded demo medication)
     */
    fun logDemoMedicationTaken() {
        viewModelScope.launch {
            _isLoading.value = true
            when (val result = repository.logMedicationTaken(
                medicationId = Constants.DEMO_MEDICATION_ID,
                seniorId = Constants.DEMO_SENIOR_ID,
                notes = "Taken via voice confirmation"
            )) {
                is Result.Success -> {
                    _medicationTaken.value = result.data
                    loadMedications()
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
            _isLoading.value = false
        }
    }

    /**
     * Load compliance data for a medication
     */
    fun loadCompliance(medicationId: String, days: Int = 7) {
        viewModelScope.launch {
            _isLoading.value = true
            when (val result = repository.getMedicationCompliance(medicationId, days)) {
                is Result.Success -> {
                    _compliance.value = result.data
                }
                is Result.Error -> {
                    _error.value = result.message
                }
                else -> {}
            }
            _isLoading.value = false
        }
    }

    /**
     * Get next medication time for a medication
     */
    fun getNextMedicationTime(medication: Medication): String? {
        return repository.getNextMedicationTime(medication)
    }

    /**
     * Check if any medications are due now
     */
    fun hasDueMedications(): Boolean {
        return _dueMedications.value.isNotEmpty()
    }

    /**
     * Get reminder message for due medication
     */
    fun getMedicationReminderMessage(): String? {
        val due = _dueMedications.value.firstOrNull() ?: return null
        return "It's time to take your ${due.medicationName}. ${due.dosage ?: ""}".trim()
    }

    /**
     * Clear medication taken state
     */
    fun clearMedicationTaken() {
        _medicationTaken.value = null
        _currentMedication.value = null
    }

    /**
     * Clear error
     */
    fun clearError() {
        _error.value = null
    }

    /**
     * Refresh medications
     */
    fun refresh() {
        loadMedications()
    }
}
