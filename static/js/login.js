document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const backendError = document.getElementById('backendError');
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    backendError.classList.add('d-none');
    backendError.innerText = '';

    // Basic validation
    let valid = true;
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
        document.getElementById('emailError').style.display = 'block';
        valid = false;
    } else {
        document.getElementById('emailError').style.display = 'none';
    }
    if (!password) {
        document.getElementById('passwordError').style.display = 'block';
        valid = false;
    } else {
        document.getElementById('passwordError').style.display = 'none';
    }

    if (!valid) return;

    const loginBtn = document.getElementById('loginBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const originalLoginHtml = loginBtn.innerHTML;
    loginBtn.disabled = true;
    // show spinner inside button
    loginBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' + originalLoginHtml;
    // disable Back button while login in progress
    if (cancelBtn) {
        cancelBtn.style.pointerEvents = 'none';
        cancelBtn.classList.add('disabled');
        cancelBtn.setAttribute('aria-disabled', 'true');
    }

    try {
        const res = await fetch('/user/api/login/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            credentials: 'include',
            body: new FormData(document.getElementById('loginForm'))
        });

        const data = await res.json();

        if (res.ok) {
            window.location.href = data.redirect_url;
        } else {
            backendError.innerText = data.detail || "Login failed";
            backendError.classList.remove('d-none');
        }
    } catch (error) {
        backendError.innerText = "Network error, please try again.";
        backendError.classList.remove('d-none');
    } finally {
        // restore button and Back button state
        loginBtn.disabled = false;
        try { loginBtn.innerHTML = originalLoginHtml; } catch (e) {}
        if (cancelBtn) {
            cancelBtn.style.pointerEvents = '';
            cancelBtn.classList.remove('disabled');
            cancelBtn.removeAttribute('aria-disabled');
        }
    }
});

// Password show/hide toggle (checkbox added to login.html)
try {
    const showPasswordToggle = document.getElementById('showPasswordToggle');
    const passwordInput = document.getElementById('password');
    if (showPasswordToggle && passwordInput) {
        showPasswordToggle.addEventListener('change', function () {
            passwordInput.type = this.checked ? 'text' : 'password';
        });
    }
} catch (e) { /* ignore if elements not present */ }