(function () {
    // Elements
    const form = document.getElementById('forgotPasswordForm');
    const backendError = document.getElementById('backendError');
    const emailInput = document.getElementById('email');
    const emailError = document.getElementById('emailError');
    const actionBtn = document.getElementById('actionBtn');

    const cancelBtn = document.getElementById('cancelBtn');
    let originalActionHtml = actionBtn ? actionBtn.innerHTML : '';

    const passwordBlock = document.getElementById('passwordBlock');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmNewPasswordInput = document.getElementById('confirmNewPassword');
    const passwordError = document.getElementById('passwordError');
    const confirmPasswordError = document.getElementById('confirmNewPasswordError');

    const otpModalEl = document.getElementById('otpModal');
    const otpModal = new bootstrap.Modal(otpModalEl);
    const otpInput = document.getElementById('otpInput');
    const otpError = document.getElementById('otpError');
    const timerDisplay = document.getElementById('timer');
    const resendOtp = document.getElementById('resendOtp');
    const otpDestination = document.getElementById('otpDestination');
    const otpCloseBtn = document.getElementById('otpCloseBtn');
    const otpCancelBtn = document.getElementById('otpCancelBtn');
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    let verifiedOtp = null;

    // Timer state (5 minutes)
    let countdown = null;
    const OTP_TTL = 300; // seconds (5 min)
    let timeLeft = OTP_TTL;

    // CSRF setup for jQuery AJAX (Django)
    function getCookie(name) {
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
    const csrftoken = getCookie('csrftoken');
    $.ajaxSetup({ headers: { 'X-CSRFToken': csrftoken } });

    // Helpers to show/hide backendError (single place for non-OTP messages)
    function showBackendError(message, type = 'danger') {
        backendError.classList.remove('d-none', 'alert-success', 'alert-danger', 'alert-warning', 'alert-info');
        backendError.classList.add('alert-' + (type || 'danger'));
        backendError.textContent = message;
    }
    function hideBackendError() {
        backendError.classList.add('d-none');
        backendError.textContent = '';
    }

        // Toast helper (consistent with other pages)
        function showToast(message, type = 'success') {
                const toastId = `toast-${Date.now()}`;
                const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
                const toastHtml = `
                <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">${message}</div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>`;
                const container = document.getElementById('toastContainer');
                if (container) container.insertAdjacentHTML('beforeend', toastHtml);
                const toastEl = document.getElementById(toastId);
                if (toastEl) {
                        const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
                        toast.show();
                        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
                }
        }

    // Field helper (for inline messages)
    function showFieldError(el, msg) {
        el.textContent = msg;
        el.style.display = 'block';
    }
    function hideFieldError(el) {
        el.style.display = 'none';
    }

    // Password validation (your regex)
    function validatePassword() {
        const value = newPasswordInput.value;
        const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}$/;
        if (!regex.test(value)) {
            showFieldError(passwordError, 'Password must be 8+ chars, incl uppercase, number & symbol');
            return false;
        }
        hideFieldError(passwordError);
        return true;
    }

    // Other validations
    function validateEmailField() {
        const v = emailInput.value.trim();
        const ok = /\S+@\S+\.\S+/.test(v);
        if (!ok) showFieldError(emailError, 'Please enter a valid email address');
        else hideFieldError(emailError);
        return ok;
    }

    function validateConfirmPassword() {
        if (newPasswordInput.value !== confirmNewPasswordInput.value) {
            showFieldError(confirmPasswordError, 'Passwords do not match');
            return false;
        }
        hideFieldError(confirmPasswordError);
        return true;
    }

    function validateOtpField() {
        const v = otpInput.value.trim();
        if (!/^\d{6}$/.test(v)) {
            showFieldError(otpError, 'Please enter a valid 6-digit code');
            return false;
        }
        hideFieldError(otpError);
        return true;
    }

    // Timer functions
    function startTimer() {
        clearInterval(countdown);
        timeLeft = OTP_TTL;
        updateTimerDisplay();
        resendOtp.style.display = 'none';
        otpInput.disabled = false;
        verifyOtpBtn.disabled = false;
        countdown = setInterval(() => {
            timeLeft -= 1;
            updateTimerDisplay();
            if (timeLeft <= 0) {
                clearInterval(countdown);
                otpInput.disabled = true;
                verifyOtpBtn.disabled = true;
                resendOtp.style.display = 'inline';
            }
        }, 1000);
    }
    function updateTimerDisplay() {
        const mm = String(Math.floor(timeLeft / 60)).padStart(2, '0');
        const ss = String(timeLeft % 60).padStart(2, '0');
        timerDisplay.textContent = `${mm}:${ss}`;
    }
    function resetTimerToFive() {
        clearInterval(countdown);
        timeLeft = OTP_TTL;
        updateTimerDisplay();
        otpInput.disabled = false;
        verifyOtpBtn.disabled = false;
        resendOtp.style.display = 'none';
        startTimer();
    }

    // API endpoints
    const URL_CHECK = '/user/api/forgot-password/check/';
    const URL_VERIFY_OTP = '/user/api/forgot-password/verify-otp/';
    const URL_RESEND_OTP = '/user/api/forgot-password/resend-otp/';
    const URL_RESET = '/user/api/forgot-password/reset/';
    const URL_CANCEL = '/user/api/forgot-password/cancel/';

    // ---------- Event bindings ----------

    // Submit email => request OTP OR (if in reset stage) perform reset
    form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        hideBackendError();
        hideFieldError(emailError);
        hideFieldError(passwordError);
        hideFieldError(confirmPasswordError);
        hideFieldError(otpError);

        const email = emailInput.value.trim();
        if (!validateEmailField()) {
            showBackendError('Please fix the errors and try again.', 'danger');
            return;
        }

        // If passwordBlock visible -> perform reset (OTP already verified)
        if (passwordBlock.style.display !== 'none') {
            if (!validatePassword() || !validateConfirmPassword()) {
                showBackendError('Please fix password errors.', 'danger');
                return;
            }

            // Show spinner and disable back while resetting
            actionBtn.disabled = true;
            try { actionBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' + originalActionHtml; } catch (e) {}
            if (cancelBtn) { cancelBtn.style.pointerEvents = 'none'; cancelBtn.classList.add('disabled'); cancelBtn.setAttribute('aria-disabled','true'); }
            $.post(URL_RESET, {
                email: email,
                new_password: newPasswordInput.value,
                otp: verifiedOtp
            }).done(function (res) {
                // show toast like registration then redirect
                showToast(res.message || 'Password reset successful...', 'success');
                setTimeout(function () { window.location.href = '/user/api/login/'; }, 1500);
            }).fail(function (xhr) {
                const msg = xhr.responseJSON?.error || 'Failed to reset password.';
                showBackendError(msg, 'danger');
            }).always(function () {
                actionBtn.disabled = false;
                try { actionBtn.innerHTML = originalActionHtml; } catch (e) {}
                if (cancelBtn) { cancelBtn.style.pointerEvents = ''; cancelBtn.classList.remove('disabled'); cancelBtn.removeAttribute('aria-disabled'); }
            });
            return;
        }

        // Normal flow: request OTP
        // Show spinner and disable back while requesting OTP
        actionBtn.disabled = true;
        try { actionBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' + originalActionHtml; } catch (e) {}
        if (cancelBtn) { cancelBtn.style.pointerEvents = 'none'; cancelBtn.classList.add('disabled'); cancelBtn.setAttribute('aria-disabled','true'); }
        $.post(URL_CHECK, { email: email })
            .done(function (res) {
                otpDestination.textContent = 'email';
                otpInput.value = '';
                hideFieldError(otpError);
                otpModal.show();
                startTimer();
                // Show OTP sent confirmation in backendError (main area)
                showBackendError(res.message || 'OTP sent. Please check your email.', 'success');
            })
            .fail(function (xhr) {
                let msg = 'Unable to start password reset.';
                if (xhr && xhr.responseJSON && xhr.responseJSON.error) msg = xhr.responseJSON.error;
                showBackendError(msg, 'danger');
            })
            .always(function () {
                actionBtn.disabled = false;
                try { actionBtn.innerHTML = originalActionHtml; } catch (e) {}
                if (cancelBtn) { cancelBtn.style.pointerEvents = ''; cancelBtn.classList.remove('disabled'); cancelBtn.removeAttribute('aria-disabled'); }
            });
    });

    // Verify OTP (inside modal) --> OTP errors must show inside modal (#otpError)
    verifyOtpBtn.addEventListener('click', function () {
        hideBackendError();            // clear main messages (ok to clear)
        hideFieldError(otpError);     // clear modal inline error
        const otpVal = otpInput.value.trim();
        const email = emailInput.value.trim();

        if (!validateOtpField()) {
            // showFieldError(otpError, ...) already called in validateOtpField
            return;
        }

        verifyOtpBtn.disabled = true;
        $.post(URL_VERIFY_OTP, { email: email, otp: otpVal })
            .done(function (res) {
                showBackendError(res.message || 'OTP verified. Enter new password.', 'success');

                emailInput.setAttribute('disabled', 'disabled');
                passwordBlock.style.display = 'block';

                // ✅ Save verified OTP for reset step
                verifiedOtp = otpVal;

                hideFieldError(otpError);
                otpModal.hide();
                actionBtn.innerHTML = 'Reset Password <i class="fas fa-arrow-right"></i>';
                // update originalActionHtml so spinner uses new label
                originalActionHtml = actionBtn.innerHTML;
                // Re-enable cancel/back now that we're in reset step
                if (cancelBtn) { cancelBtn.style.pointerEvents = ''; cancelBtn.classList.remove('disabled'); cancelBtn.removeAttribute('aria-disabled'); }
            })

            .fail(function (xhr) {
                // IMPORTANT: OTP related errors must be shown in modal's otpError, NOT backendError
                const msg = xhr && xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Invalid or expired OTP.';
                showFieldError(otpError, msg);
                // keep modal open so user can retry
                otpInput.focus();
            })
            .always(function () { verifyOtpBtn.disabled = false; });
    });

    // Resend OTP (errors should appear in modal's otpError as it's OTP-related)
    resendOtp.addEventListener('click', function (e) {
        e.preventDefault();
        hideFieldError(otpError);
        const email = emailInput.value.trim();
        if (!validateEmailField()) {
            showFieldError(otpError, 'Enter a valid email to resend OTP');
            return;
        }
        resendOtp.style.pointerEvents = 'none';
        $.post(URL_RESEND_OTP, { email: email })
            .done(function (res) {
                // success shown in main area (consistent with other success messages)
                showBackendError(res.message || 'New OTP sent to email.', 'success');
                resetTimerToFive();
            })
            .fail(function (xhr) {
                const msg = xhr && xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Failed to resend OTP.';
                // show resend failures in the modal
                showFieldError(otpError, msg);
            })
            .always(function () { resendOtp.style.pointerEvents = ''; });
    });

    // Cancel OTP / modal close -> cancel forgot-password flow (delete OTP)
    function cancelForgotFlow() {
        hideBackendError();
        const emailVal = emailInput.value.trim();
        if (!emailVal) {
            return;
        }
        $.post(URL_CANCEL, { email: emailVal })
            .done(function (res) {
                // show cancellation confirmation in main area
                showBackendError(res.message || 'Cancelled', 'warning');
            })
            .fail(function (xhr) {
                // ignore quiet failures for cancel
            });
        // reset UI modal state
        otpInput.value = '';
        hideFieldError(otpError);
        clearInterval(countdown);
        verifyOtpBtn.disabled = false;
        resendOtp.style.display = 'none';
        // restore action button and back button
        try { actionBtn.innerHTML = originalActionHtml; } catch (e) {}
        actionBtn.disabled = false;
        if (cancelBtn) { cancelBtn.style.pointerEvents = ''; cancelBtn.classList.remove('disabled'); cancelBtn.removeAttribute('aria-disabled'); }
    }

    // Bind modal close / cancel buttons
    otpCloseBtn.addEventListener('click', function () { cancelForgotFlow(); });
    otpCancelBtn.addEventListener('click', function () { cancelForgotFlow(); });

    // When modal hides, ensure OTP modal errors are cleared (so they don't appear behind modal)
    otpModalEl.addEventListener('hidden.bs.modal', function () {
        hideFieldError(otpError);
        // also re-enable verify button/input if they were disabled
        verifyOtpBtn.disabled = false;
        otpInput.disabled = false;
        resendOtp.style.display = 'none';
    });

    // ensure cleanup on page unload
    window.addEventListener('beforeunload', function () {
        clearInterval(countdown);
    });

    // Bind field-level validation listeners
    newPasswordInput && newPasswordInput.addEventListener('blur', validatePassword);
    confirmNewPasswordInput && confirmNewPasswordInput.addEventListener('blur', validateConfirmPassword);
    emailInput && emailInput.addEventListener('blur', validateEmailField);

    // Show/hide toggle for new password fields
    try {
        const showNewPasswordToggle = document.getElementById('showNewPasswordToggle');
        if (showNewPasswordToggle) {
            showNewPasswordToggle.addEventListener('change', function () {
                const t = this.checked ? 'text' : 'password';
                if (newPasswordInput) newPasswordInput.type = t;
                if (confirmNewPasswordInput) confirmNewPasswordInput.type = t;
            });
        }
    } catch (e) {}

})();