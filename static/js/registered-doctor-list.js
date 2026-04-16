$(document).ready(function() {
    // tooltips (if any)
    $('[data-bs-toggle="tooltip"]').tooltip();

    // clear search
    $('#clearSearch').on('click', function() {
        window.location.href = "" + window.location.pathname + window.location.search.split('?')[0];
        // fallback to reload without params
        window.location.href = window.location.pathname;
    });

    // auto submit when filters change
    $('#is_deleted, #is_verified, #is_subscription').on('change', function() {
        $('#searchForm').submit();
    });

    // fill doctor modal
    $('.view-doctor').on('click', function() {
        const el = $(this);
        $('#modal-name').text(el.data('name'));
        $('#modal-email').text(el.data('email'));
        $('#modal-phone').text(el.data('phone'));
        $('#modal-joined').text(el.data('joined'));

        const specs = el.data('specializations') || '';
        $('#modal-specs').text(specs || '-');

        let flags = '';
        // use loose equality to handle numeric or string data values
        if (el.data('active') == 1) flags += '<span class="badge bg-success me-1 p-2">Active</span>';
        else flags += '<span class="badge bg-warning text-dark me-1 p-2">Inactive</span>';

        if (el.data('verified') == 1) flags += '<span class="badge bg-info text-dark me-1 p-2">Verified</span>';
        else flags += '<span class="badge bg-light text-dark border me-1 p-2">Not Verified</span>';

        if (el.data('subscribed') == 1) flags += '<span class="badge bg-primary p-2">Subscribed</span>';
        else flags += '<span class="badge bg-secondary p-2">Not Subscribed</span>';

        $('#modal-flags').html(flags);

        // expanded doctor profile fields
        $('#modal-education').text(el.data('education') || '-');
        $('#modal-experience').text(el.data('experience') || '0');
        $('#modal-available').text(el.data('available') == 1 || el.data('available') === '1' ? 'Yes' : 'No');
        $('#modal-license').text(el.data('license') || '-');
        $('#modal-fee').text(el.data('fee') || '0');
        $('#modal-bio').text(el.data('bio') || '-');
        $('#modal-country').text(el.data('country') || '-');
        $('#modal-state').text(el.data('state') || '-');
        $('#modal-city').text(el.data('city') || '-');
        $('#modal-address').text(el.data('address') || '-');
        $('#modal-pincode').text(el.data('pincode') || '-');
        $('#modal-languages').text(el.data('languages') || '-');
        $('#modal-awards').text(el.data('awards') || '-');
        $('#modal-rating').text(el.data('rating_avg') || '0');
        $('#modal-reviews').text(el.data('num_reviews') || '0');
        $('#modal-subscribed').text(el.data('subscribed') == 1 || el.data('subscribed') === '1' ? 'Yes' : 'No');
        var subStart = el.data('sub_start') || '-';
        var subEnd = el.data('sub_end') || '-';
        $('#modal-sub-period').text((subStart && subStart !== '-') || (subEnd && subEnd !== '-') ? subStart + ' - ' + subEnd : '-');
        $('#modal-created').text(el.data('created_at') || '-');
        $('#modal-updated').text(el.data('updated_at') || '-');
    });

    // delete/recover action -> open confirmation modal
    let pendingAction = null; // { id: ..., action: 'delete'|'recover' }
    $('.action-delete').on('click', function(e) {
        e.preventDefault();
        pendingAction = {
            id: $(this).data('id'),
            action: $(this).data('action')
        };
        const title = pendingAction.action === 'delete' ? 'Delete Doctor' : 'Recover Doctor';
        const msg = pendingAction.action === 'delete'
            ? 'This will soft-delete the doctor. You can recover later. Continue?'
            : 'This will recover the doctor from deleted state. Continue?';

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
        const cs = (window.registeredDoctorsConfig && window.registeredDoctorsConfig.csrfToken) || '';
        const urlTemplate = (window.registeredDoctorsConfig && window.registeredDoctorsConfig.softDeleteUrlTemplate) || '';
        const url = urlTemplate ? urlTemplate.replace('0', pendingAction.id) : '';
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
                    // hide modal and reload after short delay
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
