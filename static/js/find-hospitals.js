/**
 * Find Hospitals Listing and Booking Manager
 * Handles displaying hospitals with location-based filtering, pagination, and booking functionality
 */

class FindHospitals {
    constructor(options = {}) {
        this.currentPage = options.currentPage || 1;
        this.perPage = 20;
        this.totalPages = 1;
        this.hospitals = [];
        this.selectedHospital = null;
        this.selectedDoctor = null;
        
        // Filter state - convert 'None' string to empty string
        this.filters = {
            hospital_id: (options.initialHospitalId && options.initialHospitalId !== 'None') ? options.initialHospitalId : '',
            country: (options.initialCountry && options.initialCountry !== 'None') ? options.initialCountry : '',
            state: (options.initialState && options.initialState !== 'None') ? options.initialState : '',
            city: (options.initialCity && options.initialCity !== 'None') ? options.initialCity : ''
        };
        
        // Location options
        this.locations = {
            countries: [],
            states: [],
            cities: []
        };
    }

    /**
     * Initialize the hospitals listing
     */
    init() {
        this.bindFilterEvents();
        
        // Load initial locations
        this.loadLocationOptions('country');
        
        // Load initial state if any filter is set
        if (this.filters.hospital_id || this.filters.country || this.filters.state || this.filters.city) {
            this.searchHospitals();
        }
    }

    /**
     * Bind filter change events
     */
    bindFilterEvents() {
        // Hospital change
        const hospitalSelect = document.getElementById('hospital');
        if (hospitalSelect) {
            hospitalSelect.addEventListener('change', (e) => {
                this.filters.hospital_id = e.target.value;
            });
        }
        
        // Country change
        const countrySelect = document.getElementById('country');
        if (countrySelect) {
            countrySelect.addEventListener('change', (e) => {
                this.filters.country = e.target.value;
                this.filters.state = '';
                this.filters.city = '';
                this.resetStateAndCitySelects();
                
                if (e.target.value) {
                    this.loadLocationOptions('state');
                } else {
                    this.disableSelect('state');
                    this.disableSelect('city');
                }
            });
        }
        
        // State change
        const stateSelect = document.getElementById('state');
        if (stateSelect) {
            stateSelect.addEventListener('change', (e) => {
                this.filters.state = e.target.value;
                this.filters.city = '';
                this.resetCitySelect();
                
                if (e.target.value) {
                    this.loadLocationOptions('city');
                } else {
                    this.disableSelect('city');
                }
            });
        }
        
        // City change
        const citySelect = document.getElementById('city');
        if (citySelect) {
            citySelect.addEventListener('change', (e) => {
                this.filters.city = e.target.value;
            });
        }
        
        // Search button
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.searchHospitals());
        }
        
        // Reset filters button
        const resetBtn = document.getElementById('reset-filters-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetAllFilters());
        }
    }

    /**
     * Load location options from API
     */
    async loadLocationOptions(locationType) {
        try {
            const params = new URLSearchParams({
                action: 'locations',
                type: locationType
            });
            
            if (locationType === 'state' && this.filters.country) {
                params.append('country', this.filters.country);
            }
            if (locationType === 'city' && this.filters.state) {
                params.append('state', this.filters.state);
            }
            if (locationType === 'city' && this.filters.country) {
                params.append('country', this.filters.country);
            }
            
            const response = await fetch(`/api/hospitals/?${params}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.locations) {
                this.locations[locationType === 'country' ? 'countries' : locationType === 'state' ? 'states' : 'cities'] = data.locations;
                this.populateSelect(locationType, data.locations);
                this.enableSelect(locationType);
            }
        } catch (error) {
            console.error(`Error loading ${locationType} options:`, error);
        }
    }

    /**
     * Populate select dropdown with locations
     */
    populateSelect(selectId, locations) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Clear existing options except first
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        // Add location options
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = location;
            select.appendChild(option);
        });
    }

    /**
     * Enable a select element
     */
    enableSelect(selectId) {
        const select = document.getElementById(selectId);
        if (select) {
            select.disabled = false;
        }
    }

    /**
     * Disable a select element
     */
    disableSelect(selectId) {
        const select = document.getElementById(selectId);
        if (select) {
            select.disabled = true;
            select.value = '';
        }
    }

    /**
     * Reset all filter selects
     */
    resetLocationSelects() {
        document.getElementById('country').value = '';
        document.getElementById('state').value = '';
        document.getElementById('city').value = '';
    }

    /**
     * Reset state and city selects
     */
    resetStateAndCitySelects() {
        document.getElementById('state').value = '';
        document.getElementById('city').value = '';
    }

    /**
     * Reset city select
     */
    resetCitySelect() {
        document.getElementById('city').value = '';
    }

    /**
     * Reset all filters
     */
    resetAllFilters() {
        this.filters = {
            hospital_id: '',
            country: '',
            state: '',
            city: ''
        };
        
        document.getElementById('hospital').value = '';
        this.resetLocationSelects();
        this.hideSearchResults();
        this.showInitialState();
    }

    /**
     * Search hospitals with current filters
     */
    async searchHospitals() {
        this.currentPage = 1;
        await this.loadHospitals(1);
        this.updateActiveFiltersDisplay();
    }

    /**
     * Load hospitals from API
     */
    async loadHospitals(page = 1) {
        const loadingState = document.getElementById('loading-state');
        const hospitalsContainer = document.getElementById('hospitals-container');
        const initialState = document.getElementById('initial-state');

        if (loadingState) loadingState.style.display = 'block';
        if (hospitalsContainer) hospitalsContainer.style.display = 'none';
        if (initialState) initialState.style.display = 'none';

        try {
            const params = new URLSearchParams({
                page: page,
                hospital_id: this.filters.hospital_id,
                country: this.filters.country,
                state: this.filters.state,
                city: this.filters.city
            });

            const response = await fetch(`/api/hospitals/?${params}`);
            const data = await response.json();

            if (loadingState) loadingState.style.display = 'none';

            if (data.status === 'success') {
                this.hospitals = data.hospitals;
                this.currentPage = data.page;
                this.totalPages = data.total_pages;

                if (hospitalsContainer) hospitalsContainer.style.display = 'block';

                if (this.hospitals.length > 0) {
                    this.renderHospitals(this.hospitals);
                    this.renderPagination(this.totalPages, this.currentPage);
                    document.getElementById('hospitals-count').textContent = data.total_count;
                    this.hideNoResults();
                } else {
                    this.showNoResults();
                }
            } else {
                this.showError(data.error || 'Failed to load hospitals');
            }
        } catch (error) {
            if (loadingState) loadingState.style.display = 'none';
            console.error('Error loading hospitals:', error);
            this.showError('An error occurred while loading hospitals');
        }
    }

    /**
     * Update active filters display
     */
    updateActiveFiltersDisplay() {
        const activeFiltersDiv = document.getElementById('active-filters');
        const filtersDisplay = document.getElementById('filters-display');
        
        if (!activeFiltersDiv || !filtersDisplay) return;
        
        const filters = [];
        
        if (this.filters.hospital_id) {
            const hospitalSelect = document.getElementById('hospital');
            const selectedOption = hospitalSelect.options[hospitalSelect.selectedIndex];
            filters.push(`Hospital: ${selectedOption.text}`);
        }
        if (this.filters.country) filters.push(`Country: ${this.filters.country}`);
        if (this.filters.state) filters.push(`State: ${this.filters.state}`);
        if (this.filters.city) filters.push(`City: ${this.filters.city}`);
        
        if (filters.length > 0) {
            filtersDisplay.textContent = filters.join(' | ');
            activeFiltersDiv.style.display = 'block';
        } else {
            activeFiltersDiv.style.display = 'none';
        }
    }

    /**
     * Render hospital cards in a 4x5 grid (20 per page)
     */
    renderHospitals(hospitals) {
        const grid = document.getElementById('hospitals-grid');
        if (!grid) return;

        grid.innerHTML = '';

        hospitals.forEach(hospital => {
            const card = this.createHospitalCard(hospital);
            grid.appendChild(card);
        });
        
        this.bindCardEvents();
    }

    /**
     * Create a hospital card element
     */
    createHospitalCard(hospital) {
        const col = document.createElement('div');
        col.className = 'col-lg-3 col-md-6 col-sm-12 mb-4';

        const rating = hospital.rating || 0;
        const reviews = hospital.reviews || 0;
        const stars = this.renderStars(rating);

        const emergencyBadge = hospital.emergency_services ? 
            '<span class="emergency-badge"><i class="fas fa-ambulance me-1"></i>24x7 Emergency</span>' : '';

        col.innerHTML = `
            <div class="card hospital-card h-100 position-relative">
                <div class="card-body d-flex flex-column">
                    <div class="hospital-info">
                        <h5 class="card-title mb-2">${this.escapeHtml(hospital.name)}</h5>
                        
                        <div class="hospital-rating mb-2">
                            <span class="stars text-warning">${stars}</span>
                            <span>${rating.toFixed(1)}</span>
                            <small class="text-muted">(${reviews})</small>
                        </div>

                        ${hospital.established_year ? `
                            <div class="mb-2">
                                <small class="text-muted">
                                    <i class="fas fa-calendar-alt me-1"></i>
                                    <strong>Established in:</strong> Y ${hospital.established_year} 
                                </small>
                            </div>
                        ` : ''}

                        ${hospital.medical_equipments ? `
                            <div class="mb-2">
                                <small class="text-muted">
                                    <i class="fas fa-stethoscope me-1"></i>
                                    <strong>Equipment:</strong> ${this.escapeHtml(this.truncate(hospital.medical_equipments, 50))}
                                </small>
                            </div>
                        ` : ''}

                        ${hospital.facilities ? `
                            <div class="mb-2">
                                <small class="text-muted">
                                    <i class="fas fa-hospital me-1"></i>
                                    <strong>Facilities:</strong> ${this.escapeHtml(this.truncate(hospital.facilities, 50))}
                                </small>
                            </div>
                        ` : ''}
                        ${emergencyBadge}
                    </div>
                </div>

                <div class="card-footer bg-white border-top">
                    <div class="row g-2">
                        <div class="col-12 col-md-5">
                            <button
                                class="btn btn-outline-primary w-100 btn-view-details"
                                data-hospital-id="${hospital.id}">
                                <i class="fas fa-eye me-1"></i> View Details
                            </button>
                        </div>

                        <div class="col-12 col-md-7">
                            <button
                                class="btn btn-primary w-100 btn-book-appointment"
                                data-hospital-id="${hospital.id}">
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
     * Bind card button events
     */
    bindCardEvents() {
        // View details button
        document.querySelectorAll('.btn-view-details').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const hospitalId = e.target.closest('.btn-view-details').getAttribute('data-hospital-id');
                const hospital = this.hospitals.find(h => h.id.toString() === hospitalId);
                if (hospital) {
                    this.showHospitalDetail(hospital);
                }
            });
        });

        // Book appointment button
        document.querySelectorAll('.btn-book-appointment').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const hospitalId = e.target.closest('.btn-book-appointment').getAttribute('data-hospital-id');
                const hospital = this.hospitals.find(h => h.id.toString() === hospitalId);
                if (hospital) {
                    this.selectedHospital = hospital;
                    this.bookAppointment();
                }
            });
        });

        // Book appointment from modal
        const bookBtn = document.getElementById('bookAppointmentBtn');
        if (bookBtn) {
            bookBtn.removeEventListener('click', null);
            bookBtn.addEventListener('click', () => this.bookAppointment());
        }
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
                    <a class="page-link pagination-link" data-page="${currentPage - 1}" href="#">
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
            html += `<li class="page-item"><a class="page-link pagination-link" data-page="1" href="#">1</a></li>`;
            if (startPage > 2) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                html += `<li class="page-item"><a class="page-link pagination-link" data-page="${i}" href="#">${i}</a></li>`;
            }
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
            html += `<li class="page-item"><a class="page-link pagination-link" data-page="${totalPages}" href="#">${totalPages}</a></li>`;
        }

        // Next button
        if (currentPage < totalPages) {
            html += `
                <li class="page-item">
                    <a class="page-link pagination-link" data-page="${currentPage + 1}" href="#">
                        Next<i class="fas fa-chevron-right ms-1"></i>
                    </a>
                </li>
            `;
        } else {
            html += '<li class="page-item disabled"><span class="page-link">Next</span></li>';
        }

        html += '</ul>';
        paginationContainer.innerHTML = html;
        
        // Bind pagination events
        paginationContainer.querySelectorAll('.pagination-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.getAttribute('data-page'));
                this.loadHospitals(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }

    /**
     * Show no results message
     */
    showNoResults() {
        const noResults = document.getElementById('no-results');
        const hospitalsGrid = document.getElementById('hospitals-grid');
        const paginationContainer = document.getElementById('pagination-container');

        if (noResults) noResults.style.display = 'block';
        if (hospitalsGrid) hospitalsGrid.innerHTML = '';
        if (paginationContainer) paginationContainer.innerHTML = '';
    }

    /**
     * Hide no results message
     */
    hideNoResults() {
        const noResults = document.getElementById('no-results');
        if (noResults) noResults.style.display = 'none';
    }

    /**
     * Hide search results
     */
    hideSearchResults() {
        const hospitalsContainer = document.getElementById('hospitals-container');
        if (hospitalsContainer) hospitalsContainer.style.display = 'none';
    }

    /**
     * Show initial state message
     */
    showInitialState() {
        const initialState = document.getElementById('initial-state');
        if (initialState) initialState.style.display = 'block';
    }

    /**
     * Hide initial state message
     */
    hideInitialState() {
        const initialState = document.getElementById('initial-state');
        if (initialState) initialState.style.display = 'none';
    }

    /**
     * Show error message
     */
    showError(message) {
        const grid = document.getElementById('hospitals-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">${this.escapeHtml(message)}</div>
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
     * Truncate text
     */
    truncate(text, length) {
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
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
     * Show hospital detail modal
     */
    showHospitalDetail(hospital) {
        this.selectedHospital = hospital;
        const modal = new bootstrap.Modal(document.getElementById('hospitalDetailModal'));
        const detailBody = document.getElementById('hospitalDetailBody');

        const stars = this.renderStars(hospital.rating || 0);
        
        let doctorsHtml = '';
        if (hospital.associated_doctors && hospital.associated_doctors.length > 0) {
            doctorsHtml = `
                <div class="mb-3">
                    <strong><i class="fas fa-user-md me-2"></i>Associated Doctors</strong>
                    <div class="mt-2">
                        <table class="table table-sm table-bordered mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Doctor Name</th>
                                    <th>Specialization</th>
                                    <th>Experience</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            hospital.associated_doctors.forEach(doctor => {
                doctorsHtml += `
                    <tr>
                        <td>Dr. ${this.escapeHtml(doctor.name)}</td>
                        <td>${this.escapeHtml(doctor.specializations.join(', '))}</td>
                        <td>${doctor.experience} years</td>
                    </tr>
                `;
            });
            
            doctorsHtml += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } else {
            doctorsHtml = '<p class="text-muted">No associated doctors information available.</p>';
        }

        detailBody.innerHTML = `
            <div class="hospital-detail-content">
                <h4 class="mb-3">${this.escapeHtml(hospital.name)}</h4>
                
                <div class="hospital-rating mb-3">
                    <span class="stars text-warning">${stars}</span>
                    <span class="ms-2">${hospital.rating.toFixed(1)}</span>
                    <small class="text-muted">(${hospital.reviews} reviews)</small>
                </div>

                ${hospital.emergency_services ? `
                    <div class="alert alert-info mb-3">
                        <i class="fas fa-ambulance me-2"></i>
                        <strong>24x7 Emergency Services Available</strong>
                    </div>
                ` : ''}

                ${hospital.established_year ? `
                    <div class="mb-3">
                        <strong><i class="fas fa-calendar-alt me-2"></i>Established:</strong>
                        <p>${hospital.established_year}</p>
                    </div>
                ` : ''}

                ${hospital.about_full ? `
                    <div class="mb-3">
                        <strong><i class="fas fa-info-circle me-2"></i>About:</strong>
                        <p>${this.escapeHtml(hospital.about_full)}</p>
                    </div>
                ` : ''}

                <div class="mb-3">
                    <strong><i class="fas fa-map-marker-alt me-2"></i>Address:</strong>
                    <p>${this.escapeHtml(hospital.address)}<br>
                    ${hospital.city ? this.escapeHtml(hospital.city) + ', ' : ''}${hospital.state ? this.escapeHtml(hospital.state) : ''}<br>
                    ${hospital.country ? this.escapeHtml(hospital.country) : ''} ${hospital.pincode ? '- ' + this.escapeHtml(hospital.pincode) : ''}</p>
                </div>

                <div class="mb-3">
                    <strong><i class="fas fa-phone me-2"></i>Contact:</strong>
                    <p>Phone: ${hospital.phone || 'N/A'}<br>
                    Email: ${this.escapeHtml(hospital.email)}</p>
                </div>

                ${hospital.website ? `
                    <div class="mb-3">
                        <strong><i class="fas fa-globe me-2"></i>Website:</strong>
                        <p><a href="${this.escapeHtml(hospital.website)}" target="_blank">${this.escapeHtml(hospital.website)}</a></p>
                    </div>
                ` : ''}

                ${hospital.medical_equipments ? `
                    <div class="mb-3">
                        <strong><i class="fas fa-stethoscope me-2"></i>Medical Equipment:</strong>
                        <p>${this.escapeHtml(hospital.medical_equipments)}</p>
                    </div>
                ` : ''}

                ${hospital.facilities ? `
                    <div class="mb-3">
                        <strong><i class="fas fa-hospital me-2"></i>Facilities:</strong>
                        <p>${this.escapeHtml(hospital.facilities)}</p>
                    </div>
                ` : ''}

                ${doctorsHtml}
            </div>
        `;

        modal.show();
    }

    /**
     * Book appointment - opens booking modal
     */
    bookAppointment() {
        if (!this.selectedHospital) {
            alert('Please select a hospital first');
            return;
        }

        // Close hospital detail modal
        const detailModal = bootstrap.Modal.getInstance(document.getElementById('hospitalDetailModal'));
        if (detailModal) {
            detailModal.hide();
        }

        // Populate hospital information
        document.getElementById('apptHospitalName').textContent = this.selectedHospital.name;
        document.getElementById('apptHospitalRating').textContent = this.selectedHospital.rating.toFixed(1);
        document.getElementById('apptHospitalReviews').textContent = `(${this.selectedHospital.reviews} reviews)`;
        document.getElementById('apptHospitalStars').innerHTML = this.renderStars(this.selectedHospital.rating || 0);
        
        // Format hospital address
        const addressParts = [
            this.selectedHospital.address,
            this.selectedHospital.city,
            this.selectedHospital.state,
            this.selectedHospital.country,
            this.selectedHospital.pincode
        ].filter(part => part);
        document.getElementById('apptHospitalAddress').textContent = addressParts.join(', ');

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
                        hospital_id: this.selectedHospital.id,
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
                        } else if (typeof data.errors === 'object') {
                            const firstError = Object.values(data.errors)[0];
                            errorMsg = Array.isArray(firstError) ? firstError[0] : firstError;
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

        // Remove old event listeners and add new one
        const newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
        newBtn.addEventListener('click', newHandler);
    }

    /**
     * Show booking message
     */
    showBookingMessage(message, type) {
        const messageDiv = document.getElementById('appointmentMessage');
        messageDiv.className = `alert alert-${type}`;
        messageDiv.textContent = message;
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
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FindHospitals;
}
