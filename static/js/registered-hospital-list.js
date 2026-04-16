$(document).ready(function() {
    // tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // clear search
    $('#clearSearch').on('click', function() {
        window.location.href = window.location.pathname; // go to base list URL
    });

    // auto submit when filters change
    $('#is_deleted, #is_verified, #is_subscription').on('change', function() {
        $('#searchForm').submit();
    });

    // fill hospital modal
    $('.view-hospital').on('click', function(e) {
        e.preventDefault();
        const el = $(this);
        $('#modal-name').text(el.data('name'));
        $('#modal-email').text(el.data('email'));
        $('#modal-phone').text(el.data('phone'));
        $('#modal-joined').text(el.data('joined'));

        let flags = '';
        if (el.data('active') === 1 || el.data('active') === '1') flags += '<span class="badge bg-success me-1 p-2">Active</span>';
        else flags += '<span class="badge bg-warning text-dark me-1 p-2">Inactive</span>';
        // verified
        if (el.data('verified') === 1 || el.data('verified') === '1') flags += '<span class="badge bg-info text-dark me-1 p-2">Verified</span>';
        else flags += '<span class="badge bg-light text-dark border me-1 p-2">Not Verified</span>';
        // subscribed
        if (el.data('subscribed') === 1 || el.data('subscribed') === '1') flags += '<span class="badge bg-primary p-2">Subscribed</span>';
        else flags += '<span class="badge bg-light text-dark border p-2">Not Subscribed</span>';

        $('#modal-flags').html(flags);

        // fill expanded profile fields
        $('#modal-established').text(el.data('established_year') || '-');
        $('#modal-reg-number').text(el.data('reg_number') || '-');
        $('#modal-gst-number').text(el.data('gst_number') || '-');
        $('#modal-about').text(el.data('about') || '-');
        $('#modal-country').text(el.data('country') || '-');
        var state = el.data('state') || '-';
        var city = el.data('city') || '-';
        $('#modal-state-city').text(state + ' / ' + city);
        $('#modal-address').text(el.data('address') || '-');
        $('#modal-pincode').text(el.data('pincode') || '-');
        $('#modal-website').text(el.data('website') || '-');
        $('#modal-equipments').text(el.data('medical_equipments') || '-');
        $('#modal-facilities').text(el.data('facilities') || '-');
        $('#modal-emergency').text(el.data('emergency_services') == 1 || el.data('emergency_services') === '1' ? 'Yes' : 'No');
        $('#modal-rating').text(el.data('rating_avg') || '0');
        $('#modal-reviews').text(el.data('num_reviews') || '0');
        $('#modal-subscribed').text(el.data('subscribed') == 1 || el.data('subscribed') === '1' ? 'Yes' : 'No');
        var subStart = el.data('sub_start') || '-';
        var subEnd = el.data('sub_end') || '-';
        $('#modal-sub-period').text((subStart && subStart !== '-') || (subEnd && subEnd !== '-') ? subStart + ' - ' + subEnd : '-');
        $('#modal-created').text(el.data('created_at') || '-');
        $('#modal-updated').text(el.data('updated_at') || '-');
        const modal = new bootstrap.Modal(document.getElementById('hospitalModal'));
        modal.show();
    });

    // delete/recover action -> open confirmation modal
    let pendingAction = null; // { id: ..., action: 'delete'|'recover' }
    $('.action-delete').on('click', function(e) {
        e.preventDefault();
        pendingAction = {
            id: $(this).data('id'),
            action: $(this).data('action')
        };
        const title = pendingAction.action === 'delete' ? 'Delete Hospital/Clinic' : 'Recover Hospital/Clinic';
        const msg = pendingAction.action === 'delete'
            ? 'This will soft-delete the hospital/clinic. You can recover later. Continue?'
            : 'This will recover the hospital/clinic from deleted state. Continue?';

        $('#confirmActionTitle').text(title);
        $('#confirmActionMessage').text(msg);

        if (pendingAction.action === 'delete') {
            $('#confirmActionBtn').removeClass('btn-success').addClass('btn-danger').text('Yes, Delete');
        } else {
            $('#confirmActionBtn').removeClass('btn-danger').addClass('btn-success').text('Yes, Recover');
        }

        const confirmModal = new bootstrap.Modal(document.getElementById('confirmActionModal'));
        confirmModal.show();
    });

    // confirm button -> AJAX POST
    $('#confirmActionBtn').on('click', function() {
        if (!pendingAction) return;
        const cs = typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '';
        let url = typeof SOFT_DELETE_URL !== 'undefined' ? SOFT_DELETE_URL.replace('0', pendingAction.id) : '/soft-delete-or-recover-account/' + pendingAction.id + '/';
        $.ajax({
            type: 'POST',
            url: url,
            data: {
                'action': pendingAction.action,
                'csrfmiddlewaretoken': cs
            },
            success: function(response) {
                if (response.status === 'success') {
                    showToast(response.message, 'success');
                    const cm = bootstrap.Modal.getInstance(document.getElementById('confirmActionModal'));
                    if (cm) cm.hide();
                    setTimeout(function(){ window.location.reload(); }, 800);
                } else {
                    showToast(response.message || 'Operation failed', 'danger');
                }
            },
            error: function() {
                showToast('An error occurred. Please try again.', 'danger');
            }
        });
    });

    // toast helper
    function showToast(message, type) {
        const toast = $('#statusToast');
        const toastMessage = $('#toastMessage');
        toast.removeClass('bg-success bg-danger bg-info bg-warning');
        if (type === 'success') toast.addClass('bg-success');
        else if (type === 'danger') toast.addClass('bg-danger');
        else if (type === 'info') toast.addClass('bg-info');
        else toast.addClass('bg-warning');
        toastMessage.text(message);
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();
    }
});
