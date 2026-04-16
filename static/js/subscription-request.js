/**
 * Subscription Request Stepper Form Manager
 */

class SubscriptionRequest {
    constructor(options = {}) {
        this.planId = options.planId;
        this.monthlyPrice = options.monthlyPrice;
        this.halfYearlyDiscount = options.halfYearlyDiscount;
        this.yearlyDiscount = options.yearlyDiscount;
        this.csrfToken = options.csrfToken;
        this.submitUrl = options.submitUrl;
        this.dashboardUrl = options.dashboardUrl || '/user/doctor-dashboard/';
        
        this.currentStep = 1;
        this.formData = {};
    }

    init() {
        this.bindEvents();
        this.setMinDate();
    }

    bindEvents() {
        // Step navigation
        document.getElementById('nextToStep2').addEventListener('click', () => this.goToStep2());
        document.getElementById('nextToStep3').addEventListener('click', () => this.goToStep3());
        document.getElementById('backToStep1').addEventListener('click', () => this.goToStep(1));
        document.getElementById('backToStep2').addEventListener('click', () => this.goToStep(2));

        // Duration calculation
        document.getElementById('numMonths').addEventListener('input', () => this.calculateEndDate());
        document.getElementById('startDate').addEventListener('change', () => this.calculateEndDate());

        // Image preview
        document.getElementById('paymentScreenshot').addEventListener('change', (e) => this.previewImage(e));

        // Form submission
        document.getElementById('paymentSubmissionForm').addEventListener('submit', (e) => this.handleSubmit(e));

        // Success modal close
        document.getElementById('closeSuccessModal').addEventListener('click', () => {
            window.location.href = this.dashboardUrl;
        });
    }

    setMinDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('startDate').setAttribute('min', today);
    }

    calculateEndDate() {
        const numMonths = parseInt(document.getElementById('numMonths').value);
        const startDateStr = document.getElementById('startDate').value;

        if (!numMonths || !startDateStr || numMonths < 1) {
            document.getElementById('endDate').value = '';
            return;
        }

        const startDate = new Date(startDateStr);
        const endDate = new Date(startDate);
        endDate.setMonth(endDate.getMonth() + numMonths);
        
        // Format to YYYY-MM-DD
        const endDateStr = endDate.toISOString().split('T')[0];
        document.getElementById('endDate').value = endDateStr;
    }

    validateStep1() {
        const numMonths = parseInt(document.getElementById('numMonths').value);
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (!numMonths || numMonths < 1 || numMonths > 24) {
            this.showError('Please enter a valid number of months (1-24)');
            return false;
        }

        if (!startDate) {
            this.showError('Please select a start date');
            return false;
        }

        const today = new Date().toISOString().split('T')[0];
        if (startDate < today) {
            this.showError('Start date cannot be in the past');
            return false;
        }

        if (!endDate) {
            this.showError('End date could not be calculated');
            return false;
        }

        return true;
    }

    goToStep2() {
        if (!this.validateStep1()) return;

        // Store step 1 data
        this.formData.numMonths = parseInt(document.getElementById('numMonths').value);
        this.formData.startDate = document.getElementById('startDate').value;
        this.formData.endDate = document.getElementById('endDate').value;

        // Calculate payment
        this.calculatePayment();

        // Show step 2
        this.goToStep(2);
    }

    calculatePayment() {
        const numMonths = this.formData.numMonths;
        const baseAmount = this.monthlyPrice * numMonths;
        
        let discountPercent = 0;
        if (numMonths >= 12) {
            discountPercent = this.yearlyDiscount;
        } else if (numMonths >= 6) {
            discountPercent = this.halfYearlyDiscount;
        }

        const discountAmount = Math.round((baseAmount * discountPercent) / 100);
        const finalAmount = baseAmount - discountAmount;

        // Store for submission
        this.formData.finalAmount = finalAmount;

        // Update UI
        document.getElementById('summary-duration').textContent = `${numMonths} month${numMonths > 1 ? 's' : ''}`;
        document.getElementById('summary-period').textContent = `${this.formData.startDate} to ${this.formData.endDate}`;
        document.getElementById('base-amount').textContent = `₹${baseAmount}`;
        document.getElementById('final-amount').textContent = `₹${finalAmount}`;

        if (discountPercent > 0) {
            document.getElementById('discount-row').style.display = '';
            document.getElementById('discount-percent').textContent = discountPercent;
            document.getElementById('discount-amount').textContent = `- ₹${discountAmount}`;
        } else {
            document.getElementById('discount-row').style.display = 'none';
        }
    }

    goToStep3() {
        this.goToStep(3);
    }

    goToStep(step) {
        // Hide all steps
        for (let i = 1; i <= 3; i++) {
            document.getElementById(`step-${i}`).classList.add('d-none');
            document.getElementById(`step-indicator-${i}`).querySelector('.step-number').classList.remove('active', 'completed');
        }

        // Show current step
        document.getElementById(`step-${step}`).classList.remove('d-none');
        document.getElementById(`step-indicator-${step}`).querySelector('.step-number').classList.add('active');

        // Mark previous steps as completed
        for (let i = 1; i < step; i++) {
            document.getElementById(`step-indicator-${i}`).querySelector('.step-number').classList.add('completed');
        }

        // Update progress bar
        const progress = ((step - 1) / 2) * 100;
        document.getElementById('progress-bar').style.width = `${progress}%`;

        this.currentStep = step;
    }

    previewImage(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('previewImg').src = e.target.result;
                document.getElementById('imagePreview').style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }

    async handleSubmit(event) {
        event.preventDefault();

        const paymentScreenshot = document.getElementById('paymentScreenshot').files[0];
        if (!paymentScreenshot) {
            this.showError('Please upload payment screenshot');
            return;
        }

        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';

        const formData = new FormData();
        formData.append('plan_id', this.planId);
        formData.append('start_date', this.formData.startDate);
        formData.append('end_date', this.formData.endDate);
        formData.append('duration_months', this.formData.numMonths);
        formData.append('final_amount', this.formData.finalAmount);
        formData.append('payment_screenshot', paymentScreenshot);
        formData.append('payment_message', document.getElementById('paymentMessage').value);

        try {
            const response = await fetch(this.submitUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                // Show success modal
                const successModal = new bootstrap.Modal(document.getElementById('successModal'));
                successModal.show();
            } else {
this.showError(data.message || 'Failed to submit request. Please try again.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check me-2"></i> Submit Request';
            }
        } catch (error) {
            console.error('Submission error:', error);
            this.showError('An error occurred. Please try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check me-2"></i> Submit Request';
        }
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }
}
