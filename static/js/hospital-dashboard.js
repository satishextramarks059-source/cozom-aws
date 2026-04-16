/**
 * Hospital Dashboard Manager
 * Handles availability toggle, working hours management, and dashboard interactions
 */

class HospitalDashboard {
    constructor(options = {}) {
        this.toggleEndpoint = options.toggleEndpoint;
        this.getWorkingHoursEndpoint = options.getWorkingHoursEndpoint;
        this.saveWorkingHoursEndpoint = options.saveWorkingHoursEndpoint;
        this.csrfToken = options.csrfToken;
        this.isVerified = options.isVerified || false;
        this.isAvailable = null;
        this.isLoading = false;
        this.workingHours = [];
        this.workingHoursMode = 'create'; // 'create' or 'update'
        this.hasRealData = false; // Flag to track if any real working hours data exists
    }

    /**
     * Initialize the dashboard
     */
    init() {
        this.bindEvents();
        this.setupInitialState();
        this.loadWorkingHours();
        this.bindExportBookingsEvents();
    }
    /**
     * Bind export bookings dropdown events
     */
    bindExportBookingsEvents() {
        document.querySelectorAll('.export-bookings-csv').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const status = item.getAttribute('data-status');
                this.exportBookingsCSV(status);
            });
        });
    }

    /**
     * Fetch bookings as CSV and trigger download
     */
    async exportBookingsCSV(status) {
        if (!['accepted', 'rejected'].includes(status)) return;
        try {
            const response = await fetch(`/user/api/hospital/export-bookings/?status=${status}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            if (!response.ok) {
                this.showAlert('Failed to export bookings', 'danger');
                return;
            }
            const blob = await response.blob();
            // Get filename from Content-Disposition header
            let filename = `${status}_bookings_${(new Date()).toISOString().slice(0,10)}.csv`;
            const disposition = response.headers.get('Content-Disposition');
            if (disposition && disposition.indexOf('filename=') !== -1) {
                filename = disposition.split('filename=')[1].replace(/['"]/g, '');
            }
            // Create a link and trigger download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
                a.remove();
            }, 100);
        } catch (err) {
            this.showAlert('Error exporting bookings', 'danger');
        }
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Reset Filters button for pending appointments
        const resetBtn = document.getElementById('resetPendingAppointmentsFilters');
        if (resetBtn) {
            resetBtn.addEventListener('click', function() {
                const url = new URL(window.location.href);
                url.searchParams.delete('pendingAppointmentsDateFilter');
                url.searchParams.delete('pendingAppointmentsDoctorFilter');
                window.location.href = url.toString();
            });
        }

        const toggle = document.getElementById('availabilityToggle');
        if (toggle) {
            toggle.addEventListener('change', (e) => this.handleAvailabilityToggle(e));
        }

        // Working hours modal events
        const modal = document.getElementById('workingHoursModal');
        if (modal) {
            modal.addEventListener('show.bs.modal', () => this.onModalShow());
        }

        const saveBtn = document.getElementById('saveWorkingHoursBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.handleSaveWorkingHours());
        }

        // Date filter for pending appointments
        const dateFilter = document.getElementById('pendingAppointmentsDateFilter');
        if (dateFilter) {
            dateFilter.addEventListener('change', function() {
                const selectedDate = this.value;
                const url = new URL(window.location.href);
                if (selectedDate) {
                    url.searchParams.set('pendingAppointmentsDateFilter', selectedDate);
                } else {
                    url.searchParams.delete('pendingAppointmentsDateFilter');
                }
                window.location.href = url.toString();
            });
        }

        // Doctor filter for pending appointments
        const doctorFilter = document.getElementById('pendingAppointmentsDoctorFilter');
        if (doctorFilter) {
            doctorFilter.addEventListener('change', function() {
                const selectedDoctor = this.value;
                const url = new URL(window.location.href);
                if (selectedDoctor) {
                    url.searchParams.set('pendingAppointmentsDoctorFilter', selectedDoctor);
                } else {
                    url.searchParams.delete('pendingAppointmentsDoctorFilter');
                }
                window.location.href = url.toString();
            });
        }

        // Appointment management events
        this.bindAppointmentEvents();
    }

    /**
     * Setup initial state
     */
    setupInitialState() {
        const toggle = document.getElementById('availabilityToggle');
        if (toggle) {
            this.isAvailable = toggle.checked;
            // Disable toggle if not verified
            if (!this.isVerified) {
                toggle.disabled = true;
            }
        }
    }

    /**
     * Load working hours from API
     */
    async loadWorkingHours() {
        try {
            const response = await fetch(this.getWorkingHoursEndpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.workingHours = data.working_hours;
                this.workingHoursMode = data.mode;
                // Store flag indicating if any real data exists
                this.hasRealData = data.has_data || false;
                this.updateWorkingHoursSummary();
            } else {
                console.error('Failed to load working hours');
                this.showWorkingHoursError();
            }
        } catch (error) {
            console.error('Error loading working hours:', error);
            this.showWorkingHoursError();
        }
    }

    /**
     * Show error state in working hours summary
     */
    showWorkingHoursError() {
        const summaryContainer = document.getElementById('workingHoursSummary');
        if (!summaryContainer) return;
        
        summaryContainer.innerHTML = `
            <div class="text-center py-2 mt-2">
                <i class="fas fa-exclamation-circle text-danger me-2"></i>
                <span class="text-muted">Failed to load working hours</span>
            </div>
        `;
    }

    /**
     * Update working hours summary display
     */
    updateWorkingHoursSummary() {
        const summaryContainer = document.getElementById('workingHoursSummary');
        if (!summaryContainer) return;

        // If no real data has been set yet, show empty state with CTA
        if (!this.hasRealData) {
            summaryContainer.innerHTML = `
                <div class="text-center py-2">
                    <i class="fas fa-calendar-alt text-warning me-2"></i>
                    <span class="text-muted small d-block mb-2">You haven't set your working hours yet.</span>
                    <small class="text-muted d-block">Click "Manage Availability" to add them.</small>
                </div>
            `;
            return;
        }

        // Display all days (including off days) in structured grid format
        let html = '<div class="working-hours-card-grid">';
        
        this.workingHours.forEach(day => {
            const startTimeDisplay = day.is_off ? '—' : this.formatTime(day.start_time);
            const endTimeDisplay = day.is_off ? '—' : this.formatTime(day.end_time);
            const statusDisplay = day.is_off ? '<span class="text-warning">Closed</span>' : '<span class="text-muted small">Open</span>';
            
            html += `
                <div class="working-hours-card-row">
                    <div class="wh-card-col wh-card-day">
                        <strong>${day.day_name}</strong>
                    </div>
                    <div class="wh-card-col wh-card-time">
                        <small>${startTimeDisplay}</small>
                    </div>
                    <div class="wh-card-col wh-card-time">
                        <small>${endTimeDisplay}</small>
                    </div>
                    <div class="wh-card-col wh-card-status">
                        ${statusDisplay}
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        summaryContainer.innerHTML = html;
    }

    /**
     * Format time to 12-hour format
     */
    formatTime(timeStr) {
        if (!timeStr) return '';
        const [hours, minutes] = timeStr.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minutes} ${ampm}`;
    }

    /**
     * Modal show event handler
     */
    async onModalShow() {
        // Always reload working hours data when modal opens
        await this.loadWorkingHours();
        this.renderWorkingHoursForm();
    }

    /**
     * Render working hours form
     */
    renderWorkingHoursForm() {
        const container = document.getElementById('workingHoursFormContainer');
        const titleElement = document.getElementById('modalTitle');
        
        if (!container) return;

        // If workingHours is empty or still loading, show loading state
        if (!this.workingHours || this.workingHours.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading working hours...</span>
                    </div>
                    <p class="mt-3 text-muted">Loading working hours...</p>
                </div>
            `;
            return;
        }

        // Set modal title based on mode
        if (titleElement) {
            titleElement.textContent = this.workingHoursMode === 'update' ? 'Update Working Hours' : 'Set Working Hours';
        }

        let formHtml = '<div class="working-hours-form">';

        this.workingHours.forEach((day, index) => {
            const dayId = `day-${day.day_of_week}`;
            const startTimeId = `start-time-${day.day_of_week}`;
            const endTimeId = `end-time-${day.day_of_week}`;
            const isOffId = `is-off-${day.day_of_week}`;

            formHtml += `
                <div class="working-hours-day-row mb-3 pb-3 border-bottom" data-day="${day.day_of_week}">
                    <div class="row g-2 align-items-center">
                        <div class="col-md-3">
                            <label class="form-label fw-semibold mb-2">${day.day_name}</label>
                        </div>
                        <div class="col-md-3">
                            <input type="time" 
                                class="form-control start-time-input" 
                                id="${startTimeId}"
                                value="${day.start_time || ''}"
                                title="Start Time"
                                ${day.is_off ? 'disabled' : ''}>
                        </div>
                        <div class="col-md-3">
                            <input type="time" 
                                class="form-control end-time-input" 
                                id="${endTimeId}"
                                value="${day.end_time || ''}"
                                title="End Time"
                                ${day.is_off ? 'disabled' : ''}>
                        </div>
                        <div class="col-md-3">
                            <div class="form-check">
                                <input type="checkbox" 
                                    class="form-check-input is-off-checkbox" 
                                    id="${isOffId}"
                                    ${day.is_off ? 'checked' : ''}>
                                <label class="form-check-label" for="${isOffId}">
                                    Day Off
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        formHtml += '</div>';
        container.innerHTML = formHtml;

        // Bind checkbox change events
        document.querySelectorAll('.is-off-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleDayOffToggle(e));
        });
    }

    /**
     * Handle day off toggle
     */
    handleDayOffToggle(event) {
        const checkbox = event.target;
        const dayRow = checkbox.closest('.working-hours-day-row');
        const startInput = dayRow.querySelector('.start-time-input');
        const endInput = dayRow.querySelector('.end-time-input');

        if (checkbox.checked) {
            // Day is off - disable time inputs
            startInput.disabled = true;
            endInput.disabled = true;
            startInput.value = '';
            endInput.value = '';
        } else {
            // Day is on - enable time inputs
            startInput.disabled = false;
            endInput.disabled = false;
        }

        // Clear any error messages
        dayRow.querySelectorAll('.error-message').forEach(msg => {
            msg.style.display = 'none';
            msg.textContent = '';
        });
    }

    /**
     * Validate working hours form
     */
    validateForm() {
        const formContainer = document.getElementById('workingHoursFormContainer');
        const dayRows = formContainer.querySelectorAll('.working-hours-day-row');
        let hasErrors = false;

        // Clear previous error states
        dayRows.forEach(row => {
            row.querySelectorAll('.start-time-input, .end-time-input').forEach(input => {
                input.classList.remove('is-invalid');
            });
        });

        dayRows.forEach((row, idx) => {
            const isOffCheckbox = row.querySelector('.is-off-checkbox');
            const startInput = row.querySelector('.start-time-input');
            const endInput = row.querySelector('.end-time-input');

            const isOff = isOffCheckbox.checked;
            const startTime = startInput.value;
            const endTime = endInput.value;

            if (!isOff) {
                // Validate times are provided
                if (!startTime || !endTime) {
                    hasErrors = true;
                    if (!startTime) startInput.classList.add('is-invalid');
                    if (!endTime) endInput.classList.add('is-invalid');
                }

                // Validate start < end
                if (startTime && endTime) {
                    const [startHour, startMin] = startTime.split(':');
                    const [endHour, endMin] = endTime.split(':');
                    const startMs = parseInt(startHour) * 60 + parseInt(startMin);
                    const endMs = parseInt(endHour) * 60 + parseInt(endMin);

                    if (startMs >= endMs) {
                        hasErrors = true;
                        startInput.classList.add('is-invalid');
                        endInput.classList.add('is-invalid');
                    }
                }
            }
        });

        return !hasErrors;
    }

    /**
     * Handle save working hours
     */
    async handleSaveWorkingHours() {
        // Validate form
        const isValid = this.validateForm();
        
        if (!isValid) {
            this.displayFormErrors('Please fill all required fields correctly (all active days need valid start and end times)');
            return;
        }

        // Hide error display if any
        const errorContainer = document.getElementById('formErrors');
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }

        // Collect form data
        const formContainer = document.getElementById('workingHoursFormContainer');
        const dayRows = formContainer.querySelectorAll('.working-hours-day-row');
        const workingHoursData = [];

        dayRows.forEach(row => {
            const dayNum = parseInt(row.dataset.day);
            const isOffCheckbox = row.querySelector('.is-off-checkbox');
            const startInput = row.querySelector('.start-time-input');
            const endInput = row.querySelector('.end-time-input');

            workingHoursData.push({
                day_of_week: dayNum,
                start_time: isOffCheckbox.checked ? null : startInput.value,
                end_time: isOffCheckbox.checked ? null : endInput.value,
                is_off: isOffCheckbox.checked
            });
        });

        // Send to backend
        const saveBtn = document.getElementById('saveWorkingHoursBtn');
        const originalText = saveBtn.innerHTML;
        
        try {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';

            const response = await fetch(this.saveWorkingHoursEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ working_hours: workingHoursData })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                // Update local state
                this.workingHours = workingHoursData.map((d, idx) => ({
                    ...d,
                    day_name: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][d.day_of_week]
                }));
                
                // Mark that real data has been set
                this.hasRealData = true;
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('workingHoursModal'));
                if (modal) modal.hide();

                // Show success message
                this.showAlert('Working hours saved successfully!', 'success');

                // Update summary
                this.updateWorkingHoursSummary();
            } else {
                this.displayFormErrors(data.errors || [data.message || 'Failed to save working hours']);
            }
        } catch (error) {
            console.error('Error saving working hours:', error);
            this.showAlert('An error occurred while saving working hours', 'danger');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }

    /**
     * Display form errors
     */
    displayFormErrors(errorMessage) {
        const errorContainer = document.getElementById('formErrors');
        const errorMsg = document.getElementById('errorMessage');
        
        if (errorContainer && errorMsg) {
            // Handle both string and array inputs
            if (Array.isArray(errorMessage)) {
                errorMsg.textContent = errorMessage.length > 0 ? errorMessage[0] : 'Validation error occurred';
            } else {
                errorMsg.textContent = errorMessage;
            }
            errorContainer.style.display = 'block';
            errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    /**
     * Handle availability toggle
     */
    async handleAvailabilityToggle(event) {
        if (this.isLoading || !this.isVerified) {
            event.preventDefault();
            return;
        }

        this.isLoading = true;
        const toggle = event.target;
        const loader = document.getElementById('availabilityLoader');
        const statusText = document.getElementById('availabilityText');
        
        try {
            // Disable toggle while processing
            toggle.disabled = true;
            if (loader) loader.style.display = 'block';
            
            const response = await fetch(this.toggleEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                // Update UI with new status
                this.isAvailable = data.is_available;
                toggle.checked = data.is_available;
                
                // Update status text (Open/Closed for hospital)
                if (statusText) {
                    statusText.textContent = data.is_available ? 'Open' : 'Closed';
                }
                
                // Update last updated timestamp
                if (data.last_updated) {
                    this.updateLastUpdatedTime(data.last_updated);
                }
                
                // Show success message
                this.showAlert(data.message, 'success');
            } else {
                // Revert toggle on error
                toggle.checked = this.isAvailable;
                this.showAlert('Failed to update hospital status. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Error toggling hospital status:', error);
            toggle.checked = this.isAvailable;
            this.showAlert('An error occurred. Please try again.', 'danger');
        } finally {
            toggle.disabled = false;
            if (loader) loader.style.display = 'none';
            this.isLoading = false;
        }
    }

    /**
     * Update last updated timestamp
     */
    updateLastUpdatedTime(isoTimestamp) {
        const lastUpdatedElement = document.getElementById('lastUpdated');
        if (lastUpdatedElement) {
            const date = new Date(isoTimestamp);
            const formatted = this.formatDateTime(date);
            lastUpdatedElement.textContent = formatted;
            lastUpdatedElement.title = date.toLocaleString();
        }
    }

    /**
     * Format datetime for display
     */
    formatDateTime(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) {
            return 'Just now';
        } else if (diffMins < 60) {
            return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        } else if (diffHours < 24) {
            return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        } else if (diffDays < 7) {
            return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        const container = document.getElementById('alertContainer');
        if (!container) return;
        
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        container.innerHTML = alertHtml;
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }

    /**
     * Get appropriate icon for alert type
     */
    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // ==================== Appointment Management ====================

    /**
     * Bind appointment-related events
     */
    bindAppointmentEvents() {
        // Accept appointment buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.accept-appointment-btn')) {
                const btn = e.target.closest('.accept-appointment-btn');
                const appointmentId = btn.dataset.appointmentId;
                const patientName = btn.dataset.patientName;
                this.showAcceptModal(appointmentId, patientName);
            }
        });

        // Reject appointment buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.reject-appointment-btn')) {
                const btn = e.target.closest('.reject-appointment-btn');
                const appointmentId = btn.dataset.appointmentId;
                const patientName = btn.dataset.patientName;
                this.showRejectModal(appointmentId, patientName);
            }
        });

        // Confirm accept button
        const confirmAcceptBtn = document.getElementById('confirmAcceptBtn');
        if (confirmAcceptBtn) {
            confirmAcceptBtn.addEventListener('click', () => this.handleAcceptAppointment());
        }

        // Confirm reject button
        const confirmRejectBtn = document.getElementById('confirmRejectBtn');
        if (confirmRejectBtn) {
            confirmRejectBtn.addEventListener('click', () => this.handleRejectAppointment());
        }
    }

    /**
     * Show accept appointment modal
     */
    showAcceptModal(appointmentId, patientName) {
        this.currentAppointmentId = appointmentId;
        document.getElementById('acceptPatientName').textContent = patientName;
        document.getElementById('appointmentTime').value = '';
        document.getElementById('acceptMessage').style.display = 'none';
        
        const modal = new bootstrap.Modal(document.getElementById('acceptAppointmentModal'));
        modal.show();
    }

    /**
     * Show reject appointment modal
     */
    showRejectModal(appointmentId, patientName) {
        this.currentAppointmentId = appointmentId;
        document.getElementById('rejectPatientName').textContent = patientName;
        document.getElementById('rejectionReason').value = '';
        document.getElementById('rejectMessage').style.display = 'none';
        
        const modal = new bootstrap.Modal(document.getElementById('rejectAppointmentModal'));
        modal.show();
    }

    /**
     * Handle accept appointment
     */
    async handleAcceptAppointment() {
        const appointmentTime = document.getElementById('appointmentTime').value;
        const messageDiv = document.getElementById('acceptMessage');
        const confirmBtn = document.getElementById('confirmAcceptBtn');

        if (!appointmentTime) {
            this.showModalMessage(messageDiv, 'Please select an appointment time', 'danger');
            return;
        }

        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        try {
            const response = await fetch(`/user/api/appointments/${this.currentAppointmentId}/accept/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    doctor_provided_time: appointmentTime
                })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                this.showModalMessage(messageDiv, data.message, 'success');
                
                // Remove appointment card from DOM
                setTimeout(() => {
                    this.removeAppointmentCard(this.currentAppointmentId);
                    const modal = bootstrap.Modal.getInstance(document.getElementById('acceptAppointmentModal'));
                    modal.hide();
                    this.showAlert('Appointment accepted successfully', 'success');
                }, 1500);
            } else {
                const errorMsg = data.error || data.errors?.doctor_provided_time?.[0] || 'Failed to accept appointment';
                this.showModalMessage(messageDiv, errorMsg, 'danger');
            }
        } catch (error) {
            console.error('Accept appointment error:', error);
            this.showModalMessage(messageDiv, 'An error occurred while accepting the appointment', 'danger');
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-check me-1"></i>Confirm Accept';
        }
    }

    /**
     * Handle reject appointment
     */
    async handleRejectAppointment() {
        const rejectionReason = document.getElementById('rejectionReason').value.trim();
        const messageDiv = document.getElementById('rejectMessage');
        const confirmBtn = document.getElementById('confirmRejectBtn');

        if (!rejectionReason || rejectionReason.length < 10) {
            this.showModalMessage(messageDiv, 'Please provide a rejection reason (minimum 10 characters)', 'danger');
            return;
        }

        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        try {
            const response = await fetch(`/user/api/appointments/${this.currentAppointmentId}/reject/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    rejection_reason: rejectionReason
                })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                this.showModalMessage(messageDiv, data.message, 'success');
                
                // Remove appointment card from DOM
                setTimeout(() => {
                    this.removeAppointmentCard(this.currentAppointmentId);
                    const modal = bootstrap.Modal.getInstance(document.getElementById('rejectAppointmentModal'));
                    modal.hide();
                    this.showAlert('Appointment rejected successfully', 'success');
                }, 1500);
            } else {
                const errorMsg = data.error || data.errors?.rejection_reason?.[0] || 'Failed to reject appointment';
                this.showModalMessage(messageDiv, errorMsg, 'danger');
            }
        } catch (error) {
            console.error('Reject appointment error:', error);
            this.showModalMessage(messageDiv, 'An error occurred while rejecting the appointment', 'danger');
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-times me-1"></i>Confirm Reject';
        }
    }

    /**
     * Remove appointment card from DOM
     */
    removeAppointmentCard(appointmentId) {
        const card = document.querySelector(`[data-appointment-id="${appointmentId}"]`);
        if (card) {
            card.style.transition = 'opacity 0.3s';
            card.style.opacity = '0';
            setTimeout(() => {
                card.remove();
                
                // Check if there are any appointments left
                const container = document.getElementById('appointmentsContainer');
                if (container && container.children.length === 0) {
                    // Reload page to update appointment count
                    location.reload();
                }
            }, 300);
        }
    }

    /**
     * Show message in modal
     */
    showModalMessage(messageDiv, message, type) {
        messageDiv.className = `alert alert-${type}`;
        messageDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${message}`;
        messageDiv.style.display = 'block';
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HospitalDashboard;
}
