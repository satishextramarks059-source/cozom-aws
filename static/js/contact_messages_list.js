// contact_messages_list.js
// Handles actions on the Contact Messages list: view, mark-as-read, delete, toasts

(function($){
    'use strict';

    function showToast(message, type){
        const container = document.getElementById('toastContainer');
        if(!container) return;
        const toastId = 'toast_' + Date.now();
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${type === 'success' ? 'bg-success' : 'bg-danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        container.appendChild(wrapper.firstElementChild);
        const bsToast = new bootstrap.Toast(document.getElementById(toastId));
        bsToast.show();
    }

    function performAction(messageId, action, config, onSuccess){
        const url = config.updateStatusUrl.replace('0', messageId);
        $.ajax({
            type: 'POST',
            url: url,
            data: {
                action: action,
                csrfmiddlewaretoken: config.csrfToken
            },
            success: function(response){
                if(response.status === 'success'){
                    showToast(response.message, 'success');
                    if(typeof onSuccess === 'function') onSuccess(response);
                } else {
                    showToast(response.message || 'Operation failed', 'error');
                }
            },
            error: function(){
                showToast('An error occurred. Please try again.', 'error');
            }
        });
    }

    $(document).ready(function(){
        // Expecting a global config object injected by template
        const config = window.CONTACT_MSG_CONFIG || {};
        // Initialize tooltips if available
        if(typeof bootstrap !== 'undefined'){
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (el) { return new bootstrap.Tooltip(el); });
        }

        let currentMessageId = null;
        let currentMessageStatus = null;

        // View message
        $(document).on('click', '.view-message', function(e){
            // set modal values from data attributes
            const el = $(this);
            currentMessageId = el.data('message-id');
            currentMessageStatus = el.data('message-status');

            $('#modal-name').text(el.data('message-name'));
            $('#modal-email').text(el.data('message-email'));
            $('#modal-phone').text(el.data('message-phone'));
            $('#modal-subject').text(el.data('message-subject'));
            $('#modal-content').text(el.data('message-content'));
            $('#modal-date').text(el.data('message-date'));

            // set status badge
            const status = el.data('message-status');
            let statusBadge = '';
            if (status === 'pending') {
                statusBadge = '<span class="badge bg-warning">Pending</span>';
            } else if (status === 'read') {
                statusBadge = '<span class="badge bg-info">Read</span>';
            } else {
                statusBadge = '<span class="badge bg-success">Replied</span>';
            }
            $('#modal-status').html(statusBadge);

            // update modal buttons
            updateModalButtons(status);
        });

        // Clear search button - redirect to list URL
        $(document).on('click', '#clearSearch', function(e){
            e.preventDefault();
            if(config.listUrl){
                window.location.href = config.listUrl;
            } else {
                window.location.href = window.location.pathname;
            }
        });

        // Status filter - auto submit form
        $(document).on('change', '#status', function(){
            $('#searchForm').submit();
        });

        function updateModalButtons(status){
            const markAsReadBtn = $('#markAsReadModal');
            const sendReplyBtn = $('#sendReplyModal');
            const deleteBtn = $('#deleteMessageModal');

            markAsReadBtn.prop('disabled', false).show();
            sendReplyBtn.prop('disabled', false).show();
            deleteBtn.prop('disabled', false).show();

            if(status === 'read'){
                markAsReadBtn.prop('disabled', true).hide();
            }
            if(status === 'replied'){
                // For replied messages, hide both Mark as Read and Send Reply
                sendReplyBtn.prop('disabled', true).hide();
                markAsReadBtn.prop('disabled', true).hide();
            }
        }

        // Mark as read from dropdown
        $(document).on('click', '.mark-read', function(e){
            e.preventDefault();
            const messageId = $(this).data('message-id');
            if(!messageId) return;
            performAction(messageId, 'mark_read', config, function(){
                // update row badge
                const row = $(`[data-message-id='${messageId}']`).closest('tr');
                row.find('td').eq(4).html('<span class="badge p-2 bg-info">Read</span>');
                // disable dropdown mark-read
                $(`[data-message-id='${messageId}']`).addClass('disabled').attr('aria-disabled', 'true');
            });
        });

        // Mark as read from modal
        $('#markAsReadModal').on('click', function(){
            if(!currentMessageId) return;
            performAction(currentMessageId, 'mark_read', config, function(){
                // update UI: row badge
                const row = $(`[data-message-id='${currentMessageId}']`).closest('tr');
                row.find('td').eq(4).html('<span class="badge p-2 bg-info">Read</span>');
                // Hide modal mark-as-read button
                $('#markAsReadModal').prop('disabled', true).hide();
                // hide modal
                const modalEl = document.getElementById('messageModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if(modal) modal.hide();
            });
        });

        // Delete from dropdown (no confirmation)
        $(document).on('click', '.delete-message', function(e){
            e.preventDefault();
            const messageId = $(this).data('message-id');
            if(!messageId) return;
            performAction(messageId, 'delete', config, function(){
                // reload to simplify UI update
                window.location.reload();
            });
        });

        // Delete from modal (no confirmation)
        $('#deleteMessageModal').on('click', function(){
            if(!currentMessageId) return;
            performAction(currentMessageId, 'delete', config, function(){
                window.location.reload();
            });
        });

        // Send reply from modal (navigates to reply page)
        $('#sendReplyModal').on('click', function(){
            if(currentMessageId){
                window.location.href = (config.replyToUrl || '').replace('0', currentMessageId);
            }
        });

    });

})(jQuery);
