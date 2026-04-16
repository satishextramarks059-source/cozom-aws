/**
 * Doctor Listing and Booking Manager
 * Handles displaying doctors, filtering, pagination, and booking functionality
 */

class DoctorListing {
    constructor(options = {}) {
        this.specialistId = options.specialistId;
        this.specialistName = options.specialistName;
        this.illnessName = options.illnessName;
        this.currentPage = options.currentPage || 1;
        this.perPage = 20;
        this.totalPages = 1;
        this.doctors = [];
        this.selectedDoctor = null;
    }

    /**
     * Initialize the doctor listing
     */
    init() {
        this.loadDoctors(this.currentPage);
        this.bindEvents();
    }

    /**
     * Load doctors from API
     */
    async loadDoctors(page = 1) {
        const loadingState = document.getElementById('loading-state');
        const doctorsContainer = document.getElementById('doctors-container');

        if (loadingState) loadingState.style.display = 'block';
        if (doctorsContainer) doctorsContainer.style.display = 'none';

        try {
            const url = `/api/doctors-by-specialist/?specialist_id=${this.specialistId}&page=${page}`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.status === 'success') {
                this.doctors = data.doctors;
                this.totalPages = data.total_pages;
                this.currentPage = page;

                this.renderDoctors(data.doctors);
                this.renderPagination(data.total_pages, page);

                if (doctorsContainer) doctorsContainer.style.display = 'block';
                if (loadingState) loadingState.style.display = 'none';

                if (data.doctors.length === 0) {
                    this.showNoResults();
                }
            } else {
                this.showNoResults();
                if (loadingState) loadingState.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading doctors:', error);
            this.showError('Failed to load doctors. Please try again later.');
            if (loadingState) loadingState.style.display = 'none';
        }
    }

    /**
     * Render doctor cards in a 4x4 grid
     */
    renderDoctors(doctors) {
        const grid = document.getElementById('doctors-grid');
        if (!grid) return;

        grid.innerHTML = '';

        doctors.forEach(doctor => {
            const doctorCard = this.createDoctorCard(doctor);
            grid.appendChild(doctorCard);
        });
    }

    /**
     * Create a doctor card element
     */
    createDoctorCard(doctor) {
        const col = document.createElement('div');
        col.className = 'col-lg-3 col-md-6 col-sm-12 mb-4';

        const rating = doctor.rating || 0;
        const reviews = doctor.reviews || 0;
        const stars = this.renderStars(rating);

        let hospitalSection = '';
        if (doctor.hospital) {
            hospitalSection = `
                <div class="mb-2">
                    <small class="text-muted">
                        <i class="fas fa-hospital me-1"></i>
                        <strong>${this.escapeHtml(doctor.hospital)}</strong>
                    </small>
                </div>
            `;
        }

        col.innerHTML = `
            <div class="card doctor-card h-100">
                <div class="card-body d-flex flex-column">
                    <div class="doctor-info">
                        <h5 class="card-title mb-2">Dr. ${this.escapeHtml(doctor.name)}</h5>
                        ${hospitalSection}
                        
                        <div class="doctor-rating mb-2">
                            <span class="stars text-warning">${stars}</span>
                            <span>${rating.toFixed(1)}</span>
                            <small class="text-muted">(${reviews})</small>
                        </div>

                        ${doctor.experience ? `
                            <div class="doctor-experience">
                                <strong><i class="fas fa-briefcase me-1"></i>${doctor.experience} Years</strong> Experience
                            </div>
                        ` : ''}

                        ${doctor.education ? `
                            <div class="mb-2">
                                <small class="text-muted">
                                    <i class="fas fa-graduation-cap me-1"></i>
                                    <strong>Education:</strong> ${this.escapeHtml(doctor.education)}
                                </small>
                            </div>
                        ` : ''}

                        ${doctor.languages ? `
                            <div class="mb-2">
                                <small class="text-muted">
                                    <i class="fas fa-language me-1"></i>
                                    <strong>Languages:</strong> ${this.escapeHtml(doctor.languages)}
                                </small>
                            </div>
                        ` : ''}
                    </div>

                    <div class="mt-3">
                        ${doctor.consultation_fee ? `
                            <p class="doctor-fee mb-2">₹${doctor.consultation_fee}</p>
                            <small class="text-muted">Consultation Fee</small>
                        ` : ''}
                    </div>
                </div>

                <div class="card-footer bg-white border-top">
                    <div class="row g-2">
                        <div class="col-12 col-md-5">
                            <button
                                class="btn btn-outline-primary w-100 btn-view-details"
                                data-doctor-id="${doctor.id}">
                                <i class="fas fa-eye me-1"></i> View Details
                            </button>
                        </div>

                        <div class="col-12 col-md-7">
                            <button
                                class="btn btn-primary w-100 btn-book-appointment"
                                data-doctor-id="${doctor.id}">
                                <i class="fas fa-calendar-check me-1"></i> Book Appointment
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        `;

        return col;
    }

    /**
     * Render pagination controls
     */
    renderPagination(totalPages, currentPage) {
        const paginationContainer = document.getElementById('pagination-container');
        if (!paginationContainer || totalPages <= 1) {
            if (paginationContainer) paginationContainer.innerHTML = '';
            return;
        }

        let html = '<ul class="pagination">';

        // Previous button
        if (currentPage > 1) {
            html += `
                <li class="page-item">
                    <a class="page-link pagination-link" href="#" data-page="${currentPage - 1}">
                        <i class="fas fa-chevron-left me-1"></i>Previous
                    </a>
                </li>
            `;
        } else {
            html += '<li class="page-item disabled"><span class="page-link">Previous</span></li>';
        }

        // Page numbers
        const maxPagesToShow = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);

        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        if (startPage > 1) {
            html += `<li class="page-item"><a class="page-link pagination-link" href="#" data-page="1">1</a></li>`;
            if (startPage > 2) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                html += `<li class="page-item"><a class="page-link pagination-link" href="#" data-page="${i}">${i}</a></li>`;
            }
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
            html += `<li class="page-item"><a class="page-link pagination-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
        }

        // Next button
        if (currentPage < totalPages) {
            html += `
                <li class="page-item">
                    <a class="page-link pagination-link" href="#" data-page="${currentPage + 1}">
                        Next<i class="fas fa-chevron-right ms-1"></i>
                    </a>
                </li>
            `;
        } else {
            html += '<li class="page-item disabled"><span class="page-link">Next</span></li>';
        }

        html += '</ul>';
        paginationContainer.innerHTML = html;
    }

    /**
     * Show no results message
     */
    showNoResults() {
        const noResults = document.getElementById('no-results');
        const doctorsGrid = document.getElementById('doctors-grid');
        const paginationContainer = document.getElementById('pagination-container');

        if (noResults) noResults.style.display = 'block';
        if (doctorsGrid) doctorsGrid.innerHTML = '';
        if (paginationContainer) paginationContainer.innerHTML = '';
    }

    /**
     * Show error message
     */
    showError(message) {
        const grid = document.getElementById('doctors-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            `;
        }
    }

    /**
     * Render star rating
     */
    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        let stars = '';

        for (let i = 0; i < 5; i++) {
            if (i < fullStars) {
                stars += '<i class="fas fa-star"></i>';
            } else if (i === fullStars && hasHalfStar) {
                stars += '<i class="fas fa-star-half-alt"></i>';
            } else {
                stars += '<i class="far fa-star"></i>';
            }
        }

        return stars;
    }

    /**
     * Render working hours schedule
     */
    renderWorkingHours(workingHours) {
        if (!workingHours || workingHours.length === 0) {
            return '';
        }

        // Check if any working hours are set
        const hasWorkingHours = workingHours.some(wh => wh.start_time || wh.end_time || wh.is_off);
        
        if (!hasWorkingHours) {
            return '';
        }

        let html = `
            <div class="mb-3">
                <strong><i class="fas fa-clock me-2"></i>Working Hours</strong>
                <div class="mt-2">
                    <table class="table table-sm table-bordered mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Day</th>
                                <th>Hours</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        workingHours.forEach(wh => {
            const timeDisplay = wh.is_off 
                ? '<span class="badge bg-secondary">Day Off</span>'
                : (wh.start_time && wh.end_time)
                    ? `${this.formatTime(wh.start_time)} - ${this.formatTime(wh.end_time)}`
                    : '<span class="text-muted">Not Set</span>';
            
            html += `
                <tr>
                    <td><strong>${wh.day_name}</strong></td>
                    <td>${timeDisplay}</td>
                </tr>
            `;
        });

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Format time from HH:MM to 12-hour format
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
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show doctor detail modal
     */
    showDoctorDetail(doctor) {
        this.selectedDoctor = doctor;
        const modal = new bootstrap.Modal(document.getElementById('doctorDetailModal'));
        const detailBody = document.getElementById('doctorDetailBody');

        const stars = this.renderStars(doctor.rating || 0);
        const hospitalInfo = doctor.hospital ? `
            <div class="mb-3">
                <strong><i class="fas fa-hospital me-2"></i>Hospital/Clinic:</strong>
                <p>${this.escapeHtml(doctor.hospital)}</p>
            </div>
        ` : '';

        detailBody.innerHTML = `
            <!-- Header Row -->
            <div class="row align-items-start">
                <div class="col-md-6">
                    <h5 class="mb-1">Dr. ${this.escapeHtml(doctor.name)}</h5>

                    <div class="doctor-rating mb-2">
                        <span class="stars text-warning">${stars}</span>
                        <span>${(doctor.rating || 0).toFixed(1)}</span>
                        <small class="text-muted">(${doctor.reviews || 0})</small>
                    </div>

                    <!-- Hospital Info BELOW rating -->
                    ${hospitalInfo || ''}
                </div>

                <div class="col-md-6 text-md-end">
                    ${doctor.consultation_fee ? `
                        <div>
                            <strong class="text-success" style="font-size: 1.3rem;">
                                ₹${doctor.consultation_fee}
                            </strong>
                            <p class="text-muted mb-0">Consultation Fee</p>
                        </div>
                    ` : ''}
                </div>
            </div>

            <hr>

            <!-- Two Column Details -->
            <div class="row">
                <!-- LEFT COLUMN -->
                <div class="col-md-6">

                    ${doctor.education ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-graduation-cap me-2"></i>Education
                            </strong>
                            <p class="mb-0">${this.escapeHtml(doctor.education)}</p>
                        </div>
                    ` : ''}

                    ${doctor.experience ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-briefcase me-2"></i>Experience
                            </strong>
                            <p class="mb-0">${doctor.experience} Years</p>
                        </div>
                    ` : ''}

                    ${doctor.languages ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-language me-2"></i>Languages
                            </strong>
                            <p class="mb-0">${this.escapeHtml(doctor.languages)}</p>
                        </div>
                    ` : ''}

                    ${doctor.bio ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-user-md me-2"></i>Bio
                            </strong>
                            <p class="mb-0">${this.escapeHtml(doctor.bio)}</p>
                        </div>
                    ` : ''}

                </div>

                <!-- RIGHT COLUMN -->
                <div class="col-md-6">

                    ${doctor.country ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-flag me-2"></i>Country
                            </strong>
                            <p class="mb-0">${this.escapeHtml(doctor.country)}</p>
                        </div>
                    ` : ''}

                    ${doctor.state ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-map me-2"></i>State
                            </strong>
                            <p class="mb-0">${this.escapeHtml(doctor.state)}</p>
                        </div>
                    ` : ''}

                    ${doctor.city ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-city me-2"></i>City
                            </strong>
                            <p class="mb-0">${this.escapeHtml(doctor.city)}</p>
                        </div>
                    ` : ''}

                    ${doctor.address ? `
                        <div class="mb-3">
                            <strong>
                                <i class="fas fa-map-marker-alt me-2"></i>Address
                            </strong>
                            <p class="mb-0">${this.escapeHtml(doctor.address)}</p>
                        </div>
                    ` : ''}

                </div>

            </div>

            <!-- Working Hours Section -->
            ${this.renderWorkingHours(doctor.working_hours)}

            <!-- Availability -->
            <div class="alert ${doctor.is_available ? 'alert-success' : 'alert-warning'} mt-3" role="alert">
                <i class="fas fa-circle me-2"></i>
                ${doctor.is_available ? 'Currently Available' : 'Currently Unavailable'}
            </div>
        `;


        modal.show();
    }

    /**
     * Book appointment - opens booking modal
     */
    bookAppointment() {
        if (!this.selectedDoctor) {
            alert('Please select a doctor first');
            return;
        }

        // Close doctor detail modal
        const detailModal = bootstrap.Modal.getInstance(document.getElementById('doctorDetailModal'));
        if (detailModal) {
            detailModal.hide();
        }

        // Populate booking modal with doctor info
        document.getElementById('apptDoctorName').textContent = this.selectedDoctor.name;
        document.getElementById('apptDoctorSpec').textContent = this.specialistName;
        document.getElementById('apptDoctorFee').textContent = this.selectedDoctor.consultation_fee || 'N/A';

        // Set minimum date to today (allow same-day appointments)
        const today = new Date();
        const minDate = today.toISOString().split('T')[0];
        const dateInput = document.getElementById('appointmentDate');
        dateInput.setAttribute('min', minDate);
        
        // Set maximum date to 60 days from now
        const maxDate = new Date();
        maxDate.setDate(maxDate.getDate() + 60);
        dateInput.setAttribute('max', maxDate.toISOString().split('T')[0]);

        // Reset form
        document.getElementById('appointmentBookingForm').reset();
        document.getElementById('appointmentMessage').style.display = 'none';

        // Open booking modal
        const bookingModal = new bootstrap.Modal(document.getElementById('bookAppointmentModal'));
        bookingModal.show();

        // Handle booking confirmation
        this.handleBookingConfirmation();
    }

    /**
     * Handle booking confirmation
     */
    handleBookingConfirmation() {
        const confirmBtn = document.getElementById('confirmAppointmentBtn');
        const newHandler = async (e) => {
            e.preventDefault();
            
            const appointmentDate = document.getElementById('appointmentDate').value;
            const patientMessage = document.getElementById('patientMessage').value;
            
            if (!appointmentDate) {
                this.showBookingMessage('Please select an appointment date', 'danger');
                return;
            }

            // Disable button during request
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Booking...';

            try {
                const response = await fetch('/user/api/appointments/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        doctor_id: this.selectedDoctor.id,
                        appointment_date: appointmentDate,
                        patient_message: patientMessage
                    })
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    this.showBookingMessage(data.message, 'success');
                    
                    // Close modal after 2 seconds
                    setTimeout(() => {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('bookAppointmentModal'));
                        modal.hide();
                        document.getElementById('appointmentBookingForm').reset();
                    }, 2000);
                } else {
                    // Handle various error formats from backend
                    let errorMsg = 'Failed to create appointment';
                    
                    if (data.error) {
                        errorMsg = data.error;
                    } else if (data.errors) {
                        // Handle DRF validation errors
                        if (typeof data.errors === 'string') {
                            errorMsg = data.errors;
                        } else if (Array.isArray(data.errors)) {
                            errorMsg = data.errors[0];
                        } else if (data.errors.non_field_errors) {
                            errorMsg = data.errors.non_field_errors[0];
                        } else if (data.errors.appointment_date) {
                            errorMsg = data.errors.appointment_date[0];
                        } else {
                            // Get first error from any field
                            const firstKey = Object.keys(data.errors)[0];
                            errorMsg = data.errors[firstKey][0] || data.errors[firstKey];
                        }
                    }
                    
                    this.showBookingMessage(errorMsg, 'danger');
                }
            } catch (error) {
                console.error('Booking error:', error);
                this.showBookingMessage('An error occurred while booking the appointment', 'danger');
            } finally {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '<i class="fas fa-calendar-check me-2"></i>Confirm Booking';
            }
        };

        // Remove old event listener and add new one
        confirmBtn.removeEventListener('click', confirmBtn._bookingHandler || (() => {}));
        confirmBtn._bookingHandler = newHandler;
        confirmBtn.addEventListener('click', newHandler);
    }

    /**
     * Show booking message
     */
    showBookingMessage(message, type) {
        const messageDiv = document.getElementById('appointmentMessage');
        messageDiv.className = `alert alert-${type}`;
        messageDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${message}`;
        messageDiv.style.display = 'block';
    }

    /**
     * Get CSRF token from cookies
     */
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

    /**
     * Bind event listeners
     */
    bindEvents() {
        // View details button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-view-details')) {
                const doctorId = e.target.closest('.btn-view-details').getAttribute('data-doctor-id');
                const doctor = this.doctors.find(d => d.id.toString() === doctorId);
                if (doctor) {
                    this.showDoctorDetail(doctor);
                }
            }
        });

        // Book appointment button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-book-appointment')) {
                const doctorId = e.target.closest('.btn-book-appointment').getAttribute('data-doctor-id');
                const doctor = this.doctors.find(d => d.id.toString() === doctorId);
                if (doctor) {
                    this.selectedDoctor = doctor;
                    this.bookAppointment();
                }
            }
        });

        // Book appointment from modal
        const bookBtn = document.getElementById('bookAppointmentBtn');
        if (bookBtn) {
            bookBtn.addEventListener('click', () => this.bookAppointment());
        }

        // Pagination links
        document.addEventListener('click', (e) => {
            if (e.target.closest('.pagination-link')) {
                e.preventDefault();
                const page = parseInt(e.target.closest('.pagination-link').getAttribute('data-page'));
                this.loadDoctors(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DoctorListing;
}
