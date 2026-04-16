// ---- Toast Utility ----
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
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}


document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const form = document.getElementById('hospitalRegistrationForm');
    const submitBtn = document.getElementById('submitHospitalBtn');

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
    const name = document.getElementById('name');
    const email = document.getElementById('email');
    const contactNumber = document.getElementById('contactNumber');
    const establishedYear = document.getElementById('established_year');
    const registrationNumber = document.getElementById('registration_number');
    const gstNumber = document.getElementById('gst_number');
    const about = document.getElementById('about');
    const country = document.getElementById('country');
    const state = document.getElementById('state');
    const city = document.getElementById('city');
    const address = document.getElementById('address');
    const pincode = document.getElementById('pincode');
    const website = document.getElementById('website');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmpPssword');
    const medicalEquipments = document.getElementById('medical_equipments');
    const facilities = document.getElementById('facilities');
    const emergencyServices = document.getElementById('emergency_services');

    // Timer variables
    let countdown;
    let timeLeft = 300; // 5 min

    // Helpers
    function showError(id, msg) {
        const el = document.getElementById(id);
        el.textContent = msg;
        el.style.display = 'block';
        return false;
    }
    function hideError(id) {
        document.getElementById(id).style.display = 'none';
    }

    // Validation
    function validateName() {
        if (name.value.trim().length < 2) return showError('nameError', 'Enter valid hospital name');
        hideError('nameError'); return true;
    }
    function validateEmail() {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!regex.test(email.value.trim())) return showError('emailError', 'Enter valid email');
        hideError('emailError'); return true;
    }
    function validateContact() {
        const regex = /^[6-9]\d{9}$/;
        if (!regex.test(contactNumber.value.trim())) return showError('contactNumberError', 'Enter valid 10-digit mobile');
        hideError('contactNumberError'); return true;
    }
    function validateCountry() {
        if (country.value.trim().length < 2) return showError('countryError', 'Country is required');
        hideError('countryError'); return true;
    }
    function validateState() {
        if (state.value.trim().length < 2) return showError('stateError', 'State is required');
        hideError('stateError'); return true;
    }
    function validateCity() {
        if (city.value.trim().length < 2) return showError('cityError', 'City is required');
        hideError('cityError'); return true;
    }
    function validateAddress() {
        if (address.value.trim().length < 5) return showError('addressError', 'Enter valid address');
        hideError('addressError'); return true;
    }
    function validatePincode() {
        if (pincode.value.trim().length < 4) return showError('pincodeError', 'Enter valid pincode');
        hideError('pincodeError'); return true;
    }
    function validateOtp() {
        if (!/^\d{6}$/.test(otpInput.value.trim())) return showError('otpError', 'Enter valid 6-digit OTP');
        hideError('otpError'); return true;
    }
    function validatePassword() {
        const value = password.value;
        const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;
        if (!regex.test(value)) {
            return showError('passwordError', 'Password must be 8+ chars, incl uppercase, number & symbol');
        }
        hideError('passwordError'); return true;
    }

    function validateConfirmPassword() {
        if (confirmPassword.value !== password.value) {
            return showError('confirmPasswordError', 'Passwords do not match');
        }
        hideError('confirmPasswordError'); return true;
    }

    // Additional required validations for hospital
    function validateEstablishedYear() {
        if (!establishedYear.value || String(establishedYear.value).trim().length === 0) return showError('establishedYearError', 'Established year is required');
        const y = Number(establishedYear.value);
        if (isNaN(y) || y < 1900 || y > 2099) return showError('establishedYearError', 'Enter a valid year');
        hideError('establishedYearError'); return true;
    }
    function validateRegistrationNumber() {
        if (!registrationNumber.value || registrationNumber.value.trim().length < 2) return showError('registrationNumberError', 'Registration number required');
        hideError('registrationNumberError'); return true;
    }
    function validateGST() {
        if (!gstNumber.value || gstNumber.value.trim().length < 2) return showError('gstError', 'GST number required');
        hideError('gstError'); return true;
    }
    function validateAbout() {
        if (!about.value || about.value.trim().length < 10) return showError('aboutError', 'Please provide details');
        hideError('aboutError'); return true;
    }
    function validateMedicalEquipments() {
        if (!medicalEquipments.value || medicalEquipments.value.trim().length < 2) return showError('equipmentError', 'Please list equipments');
        hideError('equipmentError'); return true;
    }
    function validateFacilities() {
        if (!facilities.value || facilities.value.trim().length < 2) return showError('facilitiesError', 'Please list facilities');
        hideError('facilitiesError'); return true;
    }

    function validateEmergencyServices() {
        if (!emergencyServices.checked) {
            return showError('emergencyServicesError', 'Please indicate if emergency services are provided');
        }
        hideError('emergencyServicesError');
        return true;
    }

    function validateForm() {
        return [
            validateName(),
            validateEmail(),
            validateContact(),
            validateCountry(),
            validateState(),
            validateCity(),
            validateAddress(),
            validatePincode(),
            validateEstablishedYear(),
            validateRegistrationNumber(),
            validateGST(),
            validateAbout(),
            validateMedicalEquipments(),
            validateFacilities(),
            validatePassword(),
            validateConfirmPassword(),
            validateEmergencyServices(),
        ].every(v => v === true);
    }

    // Timer
    function startTimer() {
        clearInterval(countdown);
        timeLeft = 300;
        updateTimerDisplay();
        countdown = setInterval(() => {
            timeLeft--; updateTimerDisplay();
            if (timeLeft <= 0) {
                clearInterval(countdown);
                otpInput.disabled = true;
                verifyOtpBtn.disabled = true;
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
        hideError('otpError'); startTimer();
    }

    // OTP method toggle
    otpEmailRadio.addEventListener('change', () => { if (otpEmailRadio.checked) otpDestination.textContent = 'email'; });
    otpPhoneRadio.addEventListener('change', () => { if (otpPhoneRadio.checked) otpDestination.textContent = 'phone'; });

    // Email uniqueness check (like patient registration)
    email.addEventListener('blur', function () {
        if (validateEmail()) {
            $.post("/user/api/check-email/", { email: email.value })
                .done(function () {
                    hideError('emailError');
                })
                .fail(function (xhr) {
                    const msg = xhr.responseJSON?.error || "Email already exists";
                    showError('emailError', msg);
                });
        }
    });

    // Contact number uniqueness check
    contactNumber.addEventListener('blur', function () {
        if (validateContact()) {
            $.post("/user/api/check-contact-number/", { contact_number: contactNumber.value })
                .done(function () {
                    hideError('contactNumberError');
                })
                .fail(function (xhr) {
                    const msg = xhr.responseJSON?.error || "Contact number already exists";
                    showError('contactNumberError', msg);
                });
        }
    });

    // Submit Registration
    submitBtn.addEventListener('click', function () {
        if (!validateForm()) {
            showToast("Please fill valida data !", "error");
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

        const data = {
            name: name.value.trim(),
            email: email.value.trim(),
            contact_number: contactNumber.value.trim(),
            country: country.value.trim(),
            state: state.value.trim(),
            city: city.value.trim(),
            address: address.value.trim(),
            pincode: pincode.value.trim(),
            address: address.value.trim(),
            password: password.value.trim()
        };

        // Optional fields
        if (establishedYear.value) data.established_year = establishedYear.value;
        if (registrationNumber.value) data.registration_number = registrationNumber.value;
        if (gstNumber.value) data.gst_number = gstNumber.value;
        if (about.value) data.about = about.value;
        if (website.value) data.website = website.value;
        if (medicalEquipments.value) data.medical_equipments = medicalEquipments.value;
        if (facilities.value) data.facilities = facilities.value;
        data.emergency_services = emergencyServices.checked;

        console.log("[Hospital] Sending registration payload:", data);

        $.post("/user/api/register/hospital/", data)
            .done(function () {
                otpDestination.textContent = document.querySelector('input[name="otpMethod"]:checked').value;
                otpModal.show(); startTimer();
                showToast("Hospital registration started. Please verify OTP.", "success");
            })
            .fail(function (xhr) {
                const msg = xhr.responseJSON?.error || "Hospital registration failed";
                showToast(msg, "error");
            })
            .always(function () {
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-loading');
            });
    });

    // Verify OTP
    verifyOtpBtn.addEventListener('click', function () {
        if (!validateOtp()) return;
        verifyOtpBtn.disabled = true;
        const selectedUserType = "hospital";

        $.post("/user/api/verify-otp/", { email: email.value, otp: otpInput.value, user_type: selectedUserType })
            .done(function () {
                showToast("Hospital account verified. Required admin approval", "success");
                setTimeout(() => window.location.href = "/user/api/login/", 2000);
            })
            .fail(function (xhr) {
                const msg = xhr.responseJSON?.error || "Invalid OTP";
                showError('otpError', msg);
                showToast(msg, "error");
                verifyOtpBtn.disabled = false;
            });
    });

    // Resend OTP
    resendOtpLink.addEventListener('click', function (e) {
        e.preventDefault();
        $.post("/user/api/resend-otp/", { email: email.value })
            .done(function () {
                resetTimer();
                showToast("New OTP sent", "success");
            })
            .fail(function () {
                showToast("Failed to resend OTP", "error");
            });
    });

    // Cancel
    document.querySelectorAll('#otpModal .btn-close, #otpModal .btn-danger').forEach(btn => {
        btn.addEventListener('click', function () {
            $.post("/user/api/cancel-registration/", { email: email.value })
                .done(() => showToast("Registration cancelled", "success"))
                .fail(() => showToast("Cancel failed", "error"));
        });
    });

    // Enhance cancel behavior: re-enable back button and stop spinner
    document.querySelectorAll('#otpModal .btn-close, #otpModal .btn-danger').forEach(btn => {
        btn.addEventListener('click', function () {
            // stop timer and reset OTP UI
            clearInterval(countdown);
            otpInput.value = '';
            resendOtpLink.style.display = 'none';
            // Re-enable submit and back buttons
            submitBtn.classList.remove('btn-loading');
            submitBtn.disabled = false;
            try {
                const backBtn = submitBtn.closest('form').querySelector('a.btn.btn-danger');
                if (backBtn) {
                    backBtn.style.pointerEvents = '';
                    backBtn.classList.remove('disabled');
                    backBtn.removeAttribute('aria-disabled');
                }
            } catch (e) {}
        });
    });

    // Password show/hide toggle
    const showPasswordToggle = document.getElementById('showPasswordToggle');
    if (showPasswordToggle) {
        showPasswordToggle.addEventListener('change', function () {
            const t = this.checked ? 'text' : 'password';
            if (password) password.type = t;
            if (confirmPassword) confirmPassword.type = t;
        });
    }

    // Real-time validation
    name.addEventListener('blur', validateName);
    contactNumber.addEventListener('blur', validateContact);
    country.addEventListener('blur', validateCountry);
    state.addEventListener('blur', validateState);
    city.addEventListener('blur', validateCity);
    address.addEventListener('blur', validateAddress);
    pincode.addEventListener('blur', validatePincode);
    password.addEventListener('blur', validatePassword);
    confirmPassword.addEventListener('blur', validateConfirmPassword);
    otpInput.addEventListener('input', () => hideError('otpError'));

    // Restrictions
    contactNumber.addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '').slice(0, 10);
    });
    otpInput.addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '').slice(0, 6);
    });
});

