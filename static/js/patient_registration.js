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
    const form = document.getElementById('patientRegistrationForm');
    const proceedBtn = document.getElementById('proceedBtn');
    const otpModal = new bootstrap.Modal(document.getElementById('otpModal'));
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    const otpInput = document.getElementById('otpInput');
    const timerDisplay = document.getElementById('timer');
    const resendOtpLink = document.getElementById('resendOtp');
    const otpDestination = document.getElementById('otpDestination');
    const otpEmailRadio = document.getElementById('otpEmail');
    const otpPhoneRadio = document.getElementById('otpPhone');

    // Form fields
    const fullName = document.getElementById('fullName');
    const dateOfBirth = document.getElementById('dateOfBirth');
    const gender = document.getElementById('gender');
    const contactNumber = document.getElementById('contactNumber');
    const email = document.getElementById('email');
    const address = document.getElementById('address');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmpPssword');

    // Optional fields 
    const emergencyContact = document.getElementById('emergency-number'); 
    const bloodGroup = document.getElementById('blood-group'); 

    // Timer variables
    let countdown;
    let timeLeft = 300; // 5 minutes

    // Debounce flag for Cancel button
    let cancelInProgress = false;

    // OTP method toggle
    otpEmailRadio.addEventListener('change', function () {
        if (this.checked) otpDestination.textContent = 'email';
    });
    otpPhoneRadio.addEventListener('change', function () {
        if (this.checked) otpDestination.textContent = 'phone';
    });

    // ------- Validation -------
    function validateFullName() {
        const value = fullName.value.trim();
        if (value.length < 2) return showError('fullNameError', 'Full name must be at least 2 characters');
        hideError('fullNameError'); return true;
    }

    function validateDateOfBirth() {
        if (!dateOfBirth.value) return showError('dateOfBirthError', 'Date of birth is required');
        const dob = new Date(dateOfBirth.value);
        if (dob > new Date()) return showError('dateOfBirthError', 'Date of birth cannot be in the future');
        hideError('dateOfBirthError'); return true;
    }

    function validateGender() {
        if (!gender.value) return showError('genderError', 'Please select your gender');
        hideError('genderError'); return true;
    }

    function validateContactNumber() {
        const regex = /^[6-9]\d{9}$/;
        if (!regex.test(contactNumber.value.trim())) return showError('contactNumberError', 'Enter valid 10-digit mobile');
        hideError('contactNumberError'); return true;
    }

    function validateEmail() {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!regex.test(email.value.trim())) return showError('emailError', 'Enter valid email');
        hideError('emailError'); return true;
    }

    // Added email uniqueness check 
    email.addEventListener('blur', function () {
        if (validateEmail()) {
            $.post("/user/api/check-email/", { email: email.value })
                .done(function (res) {
                    hideError('emailError');
                })
                .fail(function (xhr) {
                    const msg = xhr.responseJSON?.error || "Email check failed";
                    showError('emailError', msg);
                });
        }
    });

    // Added contact number uniqueness check
    contactNumber.addEventListener('blur', function () {
        if (validateContactNumber()) {
            $.post("/user/api/check-contact-number/", { contact_number: contactNumber.value })
                .done(function (res) {
                    hideError('contactNumberError');
                })
                .fail(function (xhr) {
                    const msg = xhr.responseJSON?.error || "Contact number check failed";
                    showError('contactNumberError', msg);
                });
        }
    });

    function validateAddress() {
        if (address.value.trim().length < 10) return showError('addressError', 'Please enter complete address');
        hideError('addressError'); return true;
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

    function validateOtp() {
        if (!/^\d{6}$/.test(otpInput.value.trim())) {
            return showError('otpError', 'Enter valid 6-digit OTP');
        }
        hideError('otpError'); return true;
    }

    function showError(id, msg) {
        const el = document.getElementById(id);
        el.textContent = msg; el.style.display = 'block';
        return false;
    }
    function hideError(id) {
        document.getElementById(id).style.display = 'none';
    }


    function validateEmergencyContact() {   
        if (!emergencyContact.value.trim()) return true; 
        const regex = /^[6-9]\d{9}$/;
        if (!regex.test(emergencyContact.value.trim())) {
         
            return showError('emergency-numberError', 'Enter valid 10-digit mobile');
        }

        hideError('emergency-numberError');
        return true;
    }

    function validateBloodGroup() {   
        if (!bloodGroup.value) return true; 
        hideError('blood-groupError');
        return true;
    }


    function validateForm() {
        return [
            validateFullName(),
            validateDateOfBirth(),
            validateGender(),
            validateContactNumber(),
            validateEmail(),
            validateAddress(),
            validatePassword(),
            validateConfirmPassword(),
            validateEmergencyContact(), 
            validateBloodGroup() 
        ].every(v => v === true);
    }

    // ------- Timer -------
    function startTimer() {
        clearInterval(countdown);
        timeLeft = 300; // 5 minutes
        updateTimerDisplay();
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
        hideError('otpError'); startTimer();
    }

    // ------- API Integration -------
    proceedBtn.addEventListener('click', function () {
        if (validateForm()) {
            proceedBtn.classList.add('btn-loading'); proceedBtn.disabled = true;

            // Disable the form Back button to prevent navigation during OTP flow
            const cancelBtn = document.getElementById('cancelBtn');
            if (cancelBtn) {
                cancelBtn.style.pointerEvents = 'none';
                cancelBtn.classList.add('disabled');
                cancelBtn.setAttribute('aria-disabled', 'true');
            }

            const data = {
                full_name: fullName.value,
                date_of_birth: dateOfBirth.value,
                gender: gender.value,
                contact_number: contactNumber.value,
                email: email.value,
                address: address.value,
                password: password.value
            };

            if (emergencyContact.value.trim()) {
                data.emergency_contact = emergencyContact.value.trim();
            }
            if (bloodGroup.value) {
                data.blood_group = bloodGroup.value;
            }

            $.post("/user/api/register/patient/", data)
                .done(function () {
                    otpDestination.textContent = document.querySelector('input[name="otpMethod"]:checked').value;
                    otpModal.show(); startTimer();
                    showToast("Registration started. Please verify OTP.", "success");
                })
                .fail(function (xhr) {
                    const msg = xhr.responseJSON?.error || "Something went wrong during registration.";
                    showToast(msg, "error");
                });
        }
    });

    verifyOtpBtn.addEventListener('click', function () {
        console.log("[OTP] Verify button clicked");
        console.log("OTP Value:", otpInput.value);

        if (validateOtp()) {
            console.log("[OTP] OTP validation passed");

            verifyOtpBtn.classList.add('btn-loading');
            verifyOtpBtn.disabled = true;
            const selectedUserType = "patient";

            $.post("/user/api/verify-otp/", { email: email.value, otp: otpInput.value, user_type: selectedUserType })
                .done(function () {
                    console.log("[OTP] Verification success");
                    showToast("Account verified successfully! Redirecting to login...", "success");
                    setTimeout(() => window.location.href = "/user/api/login/", 2000);
                })
                .fail(function (xhr) {
                    console.log("[OTP] Verification failed", xhr);

                    const msg = xhr.responseJSON?.error || "Invalid or expired OTP.";
                    showError('otpError', msg);
                    showToast(msg, "error");

                    // Reset submit button so user can retry 
                    verifyOtpBtn.classList.remove('btn-loading');
                    verifyOtpBtn.disabled = false;

                    console.log("[OTP] Submit button reset after error");
                });
        } else {
            console.log("[OTP] OTP validation failed");
        }
    });

    resendOtpLink.addEventListener('click', function (e) {
        e.preventDefault();
        console.log("[OTP] Resend OTP clicked");

        $.post("/user/api/resend-otp/", { email: email.value })
            .done(function () {
                console.log("[OTP] Resend OTP success");
                resetTimer();
                showToast("New OTP has been sent to your email.", "success");
            })
            .fail(function (xhr) {
                console.log("[OTP] Resend OTP failed", xhr);
                const msg = xhr.responseJSON?.error || "Failed to resend OTP.";
                showToast(msg, "error");
            });
    });

    // Attach click handler to both close and cancel buttons
    document.querySelectorAll('#otpModal .btn-close, #otpModal .btn-danger').forEach(function (btn) {
        btn.addEventListener('click', function () {
            console.log("[OTP] Cancel button clicked");

            btn.disabled = true; // Disable after click
            console.log("[OTP] Cancel button disabled");

            $.post("/user/api/cancel-registration/", { email: email.value })
                .done(function () {
                    console.log("[OTP] Cancel registration success");
                    showToast("Registration cancelled.", "success");
                    // Stop timer and reset OTP UI
                    clearInterval(countdown);
                    otpInput.value = '';
                    resendOtpLink.style.display = 'none';

                    // Re-enable main form buttons (Send OTP / Back)
                    proceedBtn.classList.remove('btn-loading');
                    proceedBtn.disabled = false;
                    const cancelBtn = document.getElementById('cancelBtn');
                    if (cancelBtn) {
                        cancelBtn.style.pointerEvents = '';
                        cancelBtn.classList.remove('disabled');
                        cancelBtn.removeAttribute('aria-disabled');
                    }
                    // Hide OTP modal if still visible
                    try { otpModal.hide(); } catch (e) {}
                })
                .fail(function (xhr) {
                    console.log("[OTP] Cancel registration failed", xhr);
                    showToast("Unable to cancel registration.", "error");

                    // Re-enable cancel button if cancel failed
                    btn.disabled = false;
                    console.log("[OTP] Cancel button re-enabled after failure");
                    // Also re-enable Send OTP so user can retry
                    proceedBtn.classList.remove('btn-loading');
                    proceedBtn.disabled = false;
                    const cancelBtn = document.getElementById('cancelBtn');
                    if (cancelBtn) {
                        cancelBtn.style.pointerEvents = '';
                        cancelBtn.classList.remove('disabled');
                        cancelBtn.removeAttribute('aria-disabled');
                    }
                });
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


    // ------- Real-time validation -------
    fullName.addEventListener('blur', validateFullName);
    dateOfBirth.addEventListener('change', validateDateOfBirth);
    gender.addEventListener('change', validateGender);
    contactNumber.addEventListener('blur', validateContactNumber);
    email.addEventListener('blur', validateEmail);
    address.addEventListener('blur', validateAddress);
    password.addEventListener('blur', validatePassword);
    confirmPassword.addEventListener('blur', validateConfirmPassword);
    otpInput.addEventListener('input', () => hideError('otpError'));

    emergencyContact.addEventListener('blur', validateEmergencyContact);
    bloodGroup.addEventListener('change', validateBloodGroup);

    contactNumber.addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '').slice(0, 10);
    });
    otpInput.addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '').slice(0, 6);
    });
});