/**
 * Patient Dashboard JavaScript
 * Handles appointment management for patients
 */

class PatientDashboard {
    constructor() {
        this.currentAppointmentId = null;
        this.cancelModal = null;
        this.viewReasonModal = null;
        this.init();
    }

    init() {
        // Initialize Bootstrap modals
        const cancelModalElement = document.getElementById('cancelAppointmentModal');
        const viewReasonModalElement = document.getElementById('viewReasonModal');
        
        if (cancelModalElement) {
            this.cancelModal = new bootstrap.Modal(cancelModalElement);
        }
        
        if (viewReasonModalElement) {
            this.viewReasonModal = new bootstrap.Modal(viewReasonModalElement);
        }

        // Bind event listeners
        this.bindEvents();
    }

    bindEvents() {
        // Cancel appointment button click
        document.querySelectorAll('.cancel-appointment-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const appointmentId = e.currentTarget.dataset.appointmentId;
                const doctorName = e.currentTarget.dataset.doctorName;
                this.showCancelModal(appointmentId, doctorName);
            });
        });

        // Confirm cancel button
        const confirmCancelBtn = document.getElementById('confirmCancelBtn');
        if (confirmCancelBtn) {
            confirmCancelBtn.addEventListener('click', () => this.handleCancelAppointment());
        }

        // View rejection reason button click
        document.querySelectorAll('.view-reason-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const reason = e.currentTarget.dataset.reason;
                this.showRejectionReason(reason);
            });
        });

        // Reset cancellation form when modal is closed
        const cancelModalElement = document.getElementById('cancelAppointmentModal');
        if (cancelModalElement) {
            cancelModalElement.addEventListener('hidden.bs.modal', () => {
                this.resetCancelForm();
            });
        }
    }

    showCancelModal(appointmentId, doctorName) {
        this.currentAppointmentId = appointmentId;
        document.getElementById('cancelDoctorName').textContent = doctorName;
        document.getElementById('cancelMessage').style.display = 'none';
        this.cancelModal.show();
    }

    async handleCancelAppointment() {
        const reasonTextarea = document.getElementById('cancellationReason');
        const reason = reasonTextarea.value.trim();

        // Validate reason
        if (!reason) {
            this.showCancelMessage('Please provide a reason for cancellation.', 'danger');
            return;
        }

        if (reason.length < 10) {
            this.showCancelMessage('Cancellation reason must be at least 10 characters long.', 'danger');
            return;
        }

        const confirmBtn = document.getElementById('confirmCancelBtn');
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Canceling...';

        try {
            const csrfToken = this.getCookie('csrftoken');
            const response = await fetch(`/user/api/appointments/${this.currentAppointmentId}/cancel/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    cancellation_reason: reason
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showCancelMessage('Appointment canceled successfully!', 'success');
                setTimeout(() => {
                    this.cancelModal.hide();
                    this.removeAppointmentRow(this.currentAppointmentId);
                }, 1500);
            } else {
                const errorMessage = data.error || data.cancellation_reason?.[0] || 'Failed to cancel appointment. Please try again.';
                this.showCancelMessage(errorMessage, 'danger');
            }
        } catch (error) {
            console.error('Error canceling appointment:', error);
            this.showCancelMessage('An error occurred. Please try again.', 'danger');
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-times me-1"></i>Confirm Cancellation';
        }
    }

    showCancelMessage(message, type) {
        const messageDiv = document.getElementById('cancelMessage');
        messageDiv.className = `alert alert-${type}`;
        messageDiv.textContent = message;
        messageDiv.style.display = 'block';
    }

    resetCancelForm() {
        document.getElementById('cancellationReason').value = '';
        document.getElementById('cancelMessage').style.display = 'none';
        this.currentAppointmentId = null;
    }

    removeAppointmentRow(appointmentId) {
        const row = document.querySelector(`tr[data-appointment-id="${appointmentId}"]`);
        if (row) {
            row.remove();
            
            // Check if table is now empty
            const tbody = document.getElementById('appointmentsTableBody');
            if (tbody && tbody.children.length === 0) {
                // Reload page to show "No appointments" message
                location.reload();
            }
        }
    }

    showRejectionReason(reason) {
        document.getElementById('rejectionReasonText').textContent = reason;
        this.viewReasonModal.show();
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PatientDashboard();
});