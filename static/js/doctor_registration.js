document.addEventListener("DOMContentLoaded", function () {
    // Make multi-select searchable
    $('#specializations').select2({
        placeholder: "Select specializations",
        allowClear: true,
        width: '100%'
    });
});

function showToast(message, type = 'success') {
    const toastId = `toast-${Date.now()}`;
    const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 mb-2" 
             role="alert" aria-live="assertive" aria-atomic="true">
          <div class="d-flex">
            <div class="toast-body">
              ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
        </div>`;

    const container = document.getElementById('toastContainer');
    container.insertAdjacentHTML('beforeend', toastHtml);

    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 6000 });
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

document.addEventListener('DOMContentLoaded', function () {
    // Elements
    const submitBtn = document.getElementById('submitDoctorBtn');

    // OTP modal elements
    const otpModal = new bootstrap.Modal(document.getElementById('otpModal'));
    const otpInput = document.getElementById('otpInput');
    const otpError = document.getElementById('otpError');
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    const timerDisplay = document.getElementById('timer');
    const resendOtpLink = document.getElementById('resendOtp');
    const otpDestination = document.getElementById('otpDestination');
    const otpEmailRadio = document.getElementById('otpEmail');
    const otpPhoneRadio = document.getElementById('otpPhone');

    // Form fields
    const doctorName = document.getElementById('doctorName');
    const email = document.getElementById('email');
    const contactNumber = document.getElementById('contactNumber');
    const education = document.getElementById('education');
    const experience = document.getElementById('experience');
    const specializations = document.getElementById('specializations');
    const licenseNumber = document.getElementById('licenseNumber');
    const consultationFee = document.getElementById('consultationFee');
    const bio = document.getElementById('bio');
    const country = document.getElementById('country');
    const state = document.getElementById('state');
    const city = document.getElementById('city');
    const address = document.getElementById('address');
    const pincode = document.getElementById('pincode');
    const languages = document.getElementById('languages');
    const awards = document.getElementById('awards');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmPassword');
    const medicalEquipments = document.getElementById('medical_equipments');
    const facilities = document.getElementById('facilities');
    const emergencyServices = document.getElementById('emergency_services');

    // Timer
    let countdown;
    let timeLeft = 300; // 5 minutes

    // CSRF via cookie (jQuery will include cookie automatically for same-origin)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(function (c) {
                const cookie = c.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');
    $.ajaxSetup({ headers: { 'X-CSRFToken': csrftoken } });

    // Helpers
    function showFieldError(id, msg) {
        const el = document.getElementById(id);
        el.textContent = msg;
        el.style.display = 'block';
    }
    function hideFieldError(id) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    }

    // Validation functions
    function validateName() {
        if (doctorName.value.trim().length < 2) return showFieldError('doctorNameError', 'Please enter your name');
        hideFieldError('doctorNameError'); return true;
    }
    function validateEmail() {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!re.test(email.value.trim())) return showFieldError('emailError', 'Enter a valid email');
        hideFieldError('emailError'); return true;
    }
    // Email uniqueness check (same as others)
    email.addEventListener('blur', function () {
        if (!validateEmail()) return;
        console.log('[Doctor] Checking email uniqueness', email.value);
        $.post('/user/api/check-email/', { email: email.value })
            .done(function () { hideFieldError('emailError'); })
            .fail(function (xhr) {
                const msg = xhr.responseJSON?.error || 'Email already exists';
                showFieldError('emailError', msg);
            });
    });

    // Contact number uniqueness check
    contactNumber.addEventListener('blur', function () {
        if (!validateContact()) return;
        console.log('[Doctor] Checking contact number uniqueness', contactNumber.value);
        $.post('/user/api/check-contact-number/', { contact_number: contactNumber.value })
            .done(function () { hideFieldError('contactNumberError'); })
            .fail(function (xhr) {
                const msg = xhr.responseJSON?.error || 'Contact number already exists';
                showFieldError('contactNumberError', msg);
            });
    });

    function validateContact() {
        const re = /^[6-9]\d{9}$/;
        if (!re.test(contactNumber.value.trim())) return showFieldError('contactNumberError', 'Enter valid 10-digit mobile');
        hideFieldError('contactNumberError'); return true;
    }
    function validateEducation() {
        if (education.value.trim().length < 2) return showFieldError('educationError', 'Enter education');
        hideFieldError('educationError'); return true;
    }
    function validateExperience() {
        const v = Number(experience.value);
        if (isNaN(v) || v < 0) return showFieldError('experienceError', 'Enter valid years of experience');
        hideFieldError('experienceError'); return true;
    }
    function validateSpecializations() {
        const selected = Array.from(specializations.selectedOptions).map(o => o.value).filter(Boolean);
        if (selected.length === 0) return showFieldError('specializationsError', 'Select at least one specialization');
        hideFieldError('specializationsError'); return true;
    }
    function validateLicense() {
        if (licenseNumber.value.trim().length < 2) return showFieldError('licenseError', 'Enter license number');
        hideFieldError('licenseError'); return true;
    }
    function validateCountry() {
        if (country.value.trim().length < 2) return showFieldError('countryError', 'Enter country');
        hideFieldError('countryError'); return true;
    }
    function validateState() {
        if (state.value.trim().length < 2) return showFieldError('stateError', 'Enter state');
        hideFieldError('stateError'); return true;
    }
    function validateCity() {
        if (city.value.trim().length < 1) return showFieldError('cityError', 'Enter city');
        hideFieldError('cityError'); return true;
    }
    function validateAddress() {
        if (address.value.trim().length < 5) return showFieldError('addressError', 'Enter address');
        hideFieldError('addressError'); return true;
    }
    function validatePincode() {
        if (pincode.value.trim().length < 3) return showFieldError('pincodeError', 'Enter pincode');
        hideFieldError('pincodeError'); return true;
    }
    function validatePassword() {
        const val = password.value;
        const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;
        if (!regex.test(val)) return showFieldError('passwordError', 'Password must be 8+ chars, incl uppercase, number & symbol');
        hideFieldError('passwordError'); return true;
    }
    function validateConfirmPassword() {
        if (confirmPassword.value !== password.value) return showFieldError('confirmPasswordError', 'Passwords do not match');
        hideFieldError('confirmPasswordError'); return true;
    }
    function validateConsultationFee() {
        if (!consultationFee.value || consultationFee.value.trim() === '') return showFieldError('consultationFeeError', 'Please enter consultation fee');
        const v = Number(consultationFee.value);
        if (isNaN(v) || v < 0) return showFieldError('consultationFeeError', 'Enter a valid fee');
        hideFieldError('consultationFeeError'); return true;
    }
    function validateLanguages() {
        if (!languages.value || languages.value.trim().length === 0) return showFieldError('languagesError', 'Please enter languages');
        hideFieldError('languagesError'); return true;
    }
    function validateOtp() {
        if (!/^\d{6}$/.test(otpInput.value.trim())) return showFieldError('otpError', 'Enter valid 6-digit OTP');
        hideFieldError('otpError'); return true;
    }

    function validateForm() {
        return [
            validateName(), validateEmail(), validateContact(),
            validateEducation(), validateExperience(), validateSpecializations(),
            validateLicense(),
            validateConsultationFee(), validateLanguages(),
            validateCountry(), validateState(), validateCity(), validateAddress(), validatePincode(),
            validatePassword(), validateConfirmPassword()
        ].every(v => v === true);
    }

    // Timer functions
    function startTimer() {
        clearInterval(countdown);
        timeLeft = 300;
        updateTimerDisplay();
        resendOtpLink.style.display = 'none';
        otpInput.disabled = false;
        verifyOtpBtn.disabled = false;
        countdown = setInterval(function () {
            timeLeft--; updateTimerDisplay();
            if (timeLeft <= 0) {
                clearInterval(countdown);
                otpInput.disabled = true; verifyOtpBtn.disabled = true;
                resendOtpLink.style.display = 'inline';
            }
        }, 1000);
    }
    function updateTimerDisplay() {
        const m = String(Math.floor(timeLeft / 60)).padStart(2, '0');
        const s = String(timeLeft % 60).padStart(2, '0');
        timerDisplay.textContent = `${m}:${s}`;
    }
    function resetTimer() {
        clearInterval(countdown);
        otpInput.disabled = false; verifyOtpBtn.disabled = false;
        resendOtpLink.style.display = 'none'; otpInput.value = '';
        hideFieldError('otpError'); startTimer();
    }

    // Submit registration
    submitBtn.addEventListener('click', function () {
        console.log('[Doctor] Register button clicked');
        if (!validateForm()) {
            console.log('[Doctor] Validation failed');
            showToast('Please fill valida data !', 'error');
            return;
        }
        submitBtn.disabled = true;
        submitBtn.classList.add('btn-loading');
        // Disable the form Back button to prevent navigation during OTP flow
        try {
            const backBtn = submitBtn.closest('form').querySelector('a.btn.btn-danger');
            if (backBtn) {
                backBtn.style.pointerEvents = 'none';
                backBtn.classList.add('disabled');
                backBtn.setAttribute('aria-disabled', 'true');
            }
        } catch (e) {}

        // Build payload
        const selectedSpecs = Array.from(specializations.selectedOptions).map(o => o.value);
        const payload = {
            doctor_name: doctorName.value.trim(),
            email: email.value.trim(),
            contact_number: contactNumber.value.trim(),
            education: education.value.trim(),
            experience: experience.value.trim(),
            specializations: selectedSpecs.join(','), // backend should parse CSV or accept list
            license_number: licenseNumber.value.trim(),
            consultation_fee: consultationFee.value ? consultationFee.value : 0,
            bio: bio.value.trim(),
            country: country.value.trim(),
            state: state.value.trim(),
            city: city.value.trim(),
            address: address.value.trim(),
            pincode: pincode.value.trim(),
            languages_spoken: languages.value.trim(),
            awards_certifications: awards.value.trim(),
            password: password.value
        };

        // Optional fields only if present
        if (medicalEquipments && medicalEquipments.value) payload.medical_equipments = medicalEquipments.value;
        if (facilities && facilities.value) payload.facilities = facilities.value;
        payload.emergency_services = emergencyServices ? emergencyServices.checked : false;

        console.log('[Doctor] Payload:', payload);

        $.post('/user/api/register/doctor/', payload)
            .done(function (res) {
                console.log('[Doctor] Registration response:', res);
                otpDestination.textContent = document.querySelector('input[name="otpMethod"]:checked').value;
                otpModal.show();
                startTimer();
                showToast('Registration started. Verify OTP to complete', 'success');
            })
            .fail(function (xhr) {
                console.error('[Doctor] Registration failed', xhr);
                const msg = xhr.responseJSON?.error || 'Registration failed';
                showToast(msg, 'error');
            })
            .always(function () {
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-loading');
            });
    });

    // Verify OTP (send user_type=doctor)
    verifyOtpBtn.addEventListener('click', function () {
        console.log('[Doctor] Verify OTP clicked');
        if (!validateOtp()) { console.log('[Doctor] OTP invalid'); return; }

        verifyOtpBtn.disabled = true;
        $.post('/user/api/verify-otp/', { email: email.value.trim(), otp: otpInput.value.trim(), user_type: 'doctor' })
            .done(function (res) {
                console.log('[Doctor] OTP verified response', res);
                showToast(res.message || 'Account verified. Required admin approval', 'success');
                setTimeout(function () { window.location.href = '/user/api/login/'; }, 2000);
            })
            .fail(function (xhr) {
                console.error('[Doctor] OTP verify failed', xhr);
                const msg = xhr.responseJSON?.error || 'Invalid or expired OTP';
                showFieldError('otpError', msg);
                showToast(msg, 'error');
                verifyOtpBtn.disabled = false;
            });
    });

    // Resend OTP
    resendOtpLink.addEventListener('click', function (e) {
        e.preventDefault();
        console.log('[Doctor] Resend OTP clicked');
        $.post('/user/api/resend-otp/', { email: email.value.trim() })
            .done(function (res) {
                console.log('[Doctor] Resend OTP OK', res);
                resetTimer();
                showToast('New OTP sent', 'success');
            })
            .fail(function (xhr) {
                console.error('[Doctor] Resend OTP failed', xhr);
                const msg = xhr.responseJSON?.error || 'Failed to resend OTP';
                showFieldError('otpError', msg);
                showToast(msg, 'error');
            });
    });

    // Cancel registration
    document.querySelectorAll('#otpModal .btn-close, #otpModal .btn-danger').forEach(function (btn) {
        btn.addEventListener('click', function () {
            console.log('[Doctor] Cancel registration clicked');
            $.post('/user/api/cancel-registration/', { email: email.value.trim() })
                .done(function () {
                    console.log('[Doctor] Cancel success');
                    showToast('Registration cancelled', 'success');
                    // stop timer and reset OTP UI
                    clearInterval(countdown);
                    otpInput.value = '';
                    resendOtpLink.style.display = 'none';
                    // Re-enable back button and submit button
                    try {
                        const backBtn = submitBtn.closest('form').querySelector('a.btn.btn-danger');
                        if (backBtn) {
                            backBtn.style.pointerEvents = '';
                            backBtn.classList.remove('disabled');
                            backBtn.removeAttribute('aria-disabled');
                        }
                    } catch (e) {}
                    submitBtn.classList.remove('btn-loading');
                    submitBtn.disabled = false;
                })
                .fail(function () {
                    console.warn('[Doctor] Cancel failed');
                    showToast('Unable to cancel registration', 'error');
                });
        });
    });

    // Real-time validation bindings
    doctorName.addEventListener('blur', validateName);
    email.addEventListener('blur', validateEmail);
    contactNumber.addEventListener('blur', validateContact);
    education.addEventListener('blur', validateEducation);
    experience.addEventListener('blur', validateExperience);
    specializations.addEventListener('change', validateSpecializations);
    licenseNumber.addEventListener('blur', validateLicense);
    country.addEventListener('blur', validateCountry);
    state.addEventListener('blur', validateState);
    city.addEventListener('blur', validateCity);
    address.addEventListener('blur', validateAddress);
    pincode.addEventListener('blur', validatePincode);
    password.addEventListener('blur', validatePassword);
    confirmPassword.addEventListener('blur', validateConfirmPassword);
    otpInput.addEventListener('input', function () { otpInput.value = otpInput.value.replace(/\D/g, '').slice(0, 6); hideFieldError('otpError'); });

    // Input restrictions
    contactNumber.addEventListener('input', function () { this.value = this.value.replace(/\D/g, '').slice(0, 10); });
    pincode.addEventListener('input', function () { this.value = this.value.replace(/[^\dA-Za-z]/g, '').slice(0, 10); });

    // Password show/hide toggle
    const showPasswordToggle = document.getElementById('showPasswordToggle');
    if (showPasswordToggle) {
        showPasswordToggle.addEventListener('change', function () {
            const t = this.checked ? 'text' : 'password';
            if (password) password.type = t;
            if (confirmPassword) confirmPassword.type = t;
        });
    }

}); // DOMContentLoaded