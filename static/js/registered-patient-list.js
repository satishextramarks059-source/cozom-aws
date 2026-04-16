$(document).ready(function() {
    // tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // clear search
    $('#clearSearch').on('click', function() {
        window.location.href = window.location.pathname; // go to base list URL
    });

    // auto submit when filters change
    $('#is_deleted, #is_subscription').on('change', function() {
        $('#searchForm').submit();
    });

    // fill patient modal
    $('.view-patient').on('click', function (e) {
        e.preventDefault();
        const el = $(this);

        $('#modal-name').text(el.data('name') || '-');
        $('#modal-email').text(el.data('email') || '-');
        $('#modal-phone').text(el.data('phone') || '-');
        $('#modal-joined').text(el.data('joined') || '-');

        $('#modal-dob').text(el.data('dob') || '-');
        $('#modal-gender').text(el.data('gender') || '-');
        $('#modal-address').text(el.data('address') || '-');
        $('#modal-emergency').text(el.data('emergency') || '-');
        $('#modal-blood').text(el.data('blood') || '-');

        // Subscription status and dates
        const isSubscribed = el.data('subscribed') === 1 || el.data('subscribed') === '1';
        const subStartDate = el.data('sub_start') || '-';
        const subEndDate = el.data('sub_end') || '-';
        
        const subBadge = isSubscribed 
            ? '<span class="badge bg-success me-1 p-2">Subscribed</span>'
            : '<span class="badge bg-warning text-dark me-1 p-2">Not Subscribed</span>';
        
        $('#modal-subscribed').html(subBadge);
        $('#modal-sub_start').text(subStartDate);
        $('#modal-sub_end').text(subEndDate);

        let flags = '';
        if (el.data('active') === 1 || el.data('active') === '1') {
            flags += '<span class="badge bg-success me-1 p-2">Active</span>';
        } else {
            flags += '<span class="badge bg-warning text-dark me-1 p-2">Inactive</span>';
        }

        $('#modal-flags').html(flags);

        const modal = new bootstrap.Modal(document.getElementById('patientModal'));
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
        const title = pendingAction.action === 'delete' ? 'Delete Patient' : 'Recover Patient';
        const msg = pendingAction.action === 'delete'
            ? 'This will soft-delete the patient. You can recover later. Continue?'
            : 'This will recover the patient from deleted state. Continue?';

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
