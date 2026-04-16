/**
 * Registered Doctor Listing and Booking Manager
 * Handles displaying registered doctors with location-based filtering, pagination, and booking functionality
 */

class RegisteredDoctorListing {
    constructor(options = {}) {
        this.currentPage = options.currentPage || 1;
        this.perPage = 20;
        this.totalPages = 1;
        this.doctors = [];
        this.selectedDoctor = null;
        
        // Filter state - convert 'None' string to empty string
        this.filters = {
            specialization_id: (options.initialSpecialization && options.initialSpecialization !== 'None') ? options.initialSpecialization : '',
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
     * Initialize the registered doctor listing
     */
    init() {
        this.bindFilterEvents();
        
        // Load initial state if specialization is set
        if (this.filters.specialization_id) {
            this.loadLocationOptions('country');
            if (this.filters.country) {
                this.loadLocationOptions('state');
                if (this.filters.state) {
                    this.loadLocationOptions('city');
                }
            }
            this.searchDoctors();
        }
    }

    /**
     * Bind filter change events
     */
    bindFilterEvents() {
        // Specialization change
        const specializationSelect = document.getElementById('specialization');
        if (specializationSelect) {
            specializationSelect.addEventListener('change', (e) => {
                this.filters.specialization_id = e.target.value;
                this.filters.country = '';
                this.filters.state = '';
                this.filters.city = '';
                
                this.resetLocationSelects();
                
                if (this.filters.specialization_id) {
                    this.enableSelect('country');
                    this.loadLocationOptions('country');
                } else {
                    this.disableAllLocationSelects();
                    this.hideInitialState();
                }
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
                
                if (this.filters.country) {
                    this.enableSelect('state');
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
                
                if (this.filters.state) {
                    this.enableSelect('city');
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
            searchBtn.addEventListener('click', () => this.searchDoctors());
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
            let url = `/api/registered-doctors/?action=locations&type=${locationType}&specialization_id=${this.filters.specialization_id}`;
            
            if (locationType === 'state' && this.filters.country) {
                url += `&country=${encodeURIComponent(this.filters.country)}`;
            } else if (locationType === 'city' && this.filters.country && this.filters.state) {
                url += `&country=${encodeURIComponent(this.filters.country)}&state=${encodeURIComponent(this.filters.state)}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.locations[locationType === 'country' ? 'countries' : 
                              locationType === 'state' ? 'states' : 'cities'] = data.locations;
                this.populateSelect(locationType, data.locations);
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
            select.classList.remove('opacity-50');
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
            select.classList.add('opacity-50');
        }
    }

    /**
     * Disable all location selects
     */
    disableAllLocationSelects() {
        this.disableSelect('country');
        this.disableSelect('state');
        this.disableSelect('city');
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
            specialization_id: '',
            country: '',
            state: '',
            city: ''
        };
        
        document.getElementById('specialization').value = '';
        this.resetLocationSelects();
        this.disableAllLocationSelects();
        this.hideSearchResults();
        this.showInitialState();
    }

    /**
     * Search doctors with current filters
     */
    async searchDoctors() {
        if (!this.filters.specialization_id) {
            alert('Please select a specialization');
            return;
        }
        
        this.currentPage = 1;
        await this.loadDoctors(1);
        this.updateActiveFiltersDisplay();
    }

    /**
     * Load doctors from API
     */
    async loadDoctors(page = 1) {
        const loadingState = document.getElementById('loading-state');
        const doctorsContainer = document.getElementById('doctors-container');
        const initialState = document.getElementById('initial-state');

        if (loadingState) loadingState.style.display = 'block';
        if (doctorsContainer) doctorsContainer.style.display = 'none';
        if (initialState) initialState.style.display = 'none';

        try {
            let url = `/api/registered-doctors/?specialization_id=${this.filters.specialization_id}&page=${page}`;
            
            if (this.filters.country) {
                url += `&country=${encodeURIComponent(this.filters.country)}`;
            }
            if (this.filters.state) {
                url += `&state=${encodeURIComponent(this.filters.state)}`;
            }
            if (this.filters.city) {
                url += `&city=${encodeURIComponent(this.filters.city)}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.status === 'success') {
                // Normalize doctor objects for booking modal compatibility
                this.doctors = data.doctors.map(doc => {
                    // If 'doctor_name' missing, use 'name'
                    if (!doc.doctor_name && doc.name) doc.doctor_name = doc.name;
                    // If 'specializations' is a string, convert to array
                    if (doc.specializations && typeof doc.specializations === 'string') {
                        doc.specializations = doc.specializations.split(',').map(s => s.trim());
                    }
                    // If 'specializations' is undefined, set to empty array
                    if (!doc.specializations) doc.specializations = [];
                    return doc;
                });
                this.totalPages = data.total_pages;
                this.currentPage = page;

                this.renderDoctors(this.doctors);
                this.renderPagination(data.total_pages, page);
                
                document.getElementById('doctors-count').textContent = data.total_count;

                if (doctorsContainer) doctorsContainer.style.display = 'block';
                if (loadingState) loadingState.style.display = 'none';

                if (this.doctors.length === 0) {
                    this.showNoResults();
                } else {
                    this.hideNoResults();
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
     * Update active filters display
     */
    updateActiveFiltersDisplay() {
        const activeFiltersDiv = document.getElementById('active-filters');
        const filtersDisplay = document.getElementById('filters-display');
        
        if (!activeFiltersDiv || !filtersDisplay) return;
        
        const filters = [];
        
        if (this.filters.specialization_id) {
            const spec = document.querySelector(`#specialization option[value="${this.filters.specialization_id}"]`);
            if (spec) filters.push(`Specialization: ${spec.textContent}`);
        }
        if (this.filters.country) filters.push(`Country: ${this.filters.country}`);
        if (this.filters.state) filters.push(`State: ${this.filters.state}`);
        if (this.filters.city) filters.push(`City: ${this.filters.city}`);
        
        if (filters.length > 0) {
            filtersDisplay.innerHTML = filters.join(' | ');
            activeFiltersDiv.style.display = 'block';
        } else {
            activeFiltersDiv.style.display = 'none';
        }
    }

    /**
     * Render doctor cards in a 4x5 grid (20 per page)
     */
    renderDoctors(doctors) {
        const grid = document.getElementById('doctors-grid');
        if (!grid) return;

        grid.innerHTML = '';

        doctors.forEach(doctor => {
            const doctorCard = this.createDoctorCard(doctor);
            grid.appendChild(doctorCard);
        });
        
        this.bindCardEvents();
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
     * Bind card button events
     */
    bindCardEvents() {
        // View details button
        document.querySelectorAll('.btn-view-details').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const doctorId = btn.getAttribute('data-doctor-id');
                const doctor = this.doctors.find(d => d.id.toString() === doctorId);
                if (doctor) {
                    this.showDoctorDetail(doctor);
                }
            });
        });

        // Book appointment button
        document.querySelectorAll('.btn-book-appointment').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const doctorId = btn.getAttribute('data-doctor-id');
                const doctor = this.doctors.find(d => d.id.toString() === doctorId);
                if (doctor) {
                    this.selectedDoctor = doctor;
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
        
        // Bind pagination events
        paginationContainer.querySelectorAll('.pagination-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.getAttribute('data-page'));
                this.loadDoctors(page);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
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
        const doctorsContainer = document.getElementById('doctors-container');
        if (doctorsContainer) doctorsContainer.style.display = 'none';
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
        document.getElementById('apptDoctorName').textContent = this.selectedDoctor.doctor_name;
        document.getElementById('apptDoctorSpec').textContent = this.selectedDoctor.specializations.join(', ');
        document.getElementById('apptDoctorFee').textContent = this.selectedDoctor.consultation_fee;

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
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RegisteredDoctorListing;
}
