(function($){
    'use strict';

    function showToast(message, type){
        const container = document.getElementById('toastContainer');
        if(!container) return;
        
        const toastId = 'toast_' + Date.now();
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${type === 'success' ? 'bg-success' : 'bg-danger'} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        container.appendChild(wrapper.firstElementChild);
        const bsToast = new bootstrap.Toast(document.getElementById(toastId), {
            autohide: true,
            delay: 3000
        });
        bsToast.show();
        
        // Remove toast after it's hidden
        document.getElementById(toastId).addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    }

    function formatCurrency(amount) {
        if (amount === undefined || amount === null || amount === '') return 'Rs. 0';
        return 'Rs. ' + parseInt(amount).toLocaleString('en-IN');
    }

    function performDelete(planId, config, onSuccess){
        const url = config.deleteUrl.replace('0', planId);
        
        // Show loading state
        $('#confirmDeleteBtn').html('<i class="fas fa-spinner fa-spin me-2"></i>Deleting...').prop('disabled', true);
        
        $.ajax({
            type: 'POST',
            url: url,
            data: { 
                csrfmiddlewaretoken: config.csrfToken 
            },
            success: function(response){
                $('#confirmDeleteBtn').html('Delete Plan').prop('disabled', false);
                
                if(response.status === 'success'){
                    showToast(response.message, 'success');
                    
                    // Close modal
                    const modalEl = document.getElementById('confirmDeleteModal');
                    if(modalEl){
                        const modalInstance = bootstrap.Modal.getInstance(modalEl);
                        if(modalInstance) modalInstance.hide();
                    }
                    
                    // Remove row from table
                    const row = $(`tr[data-plan-id='${planId}']`);
                    if(row.length){
                        row.fadeOut(300, function(){
                            $(this).remove();
                            // Check if table is empty after deletion
                            if($('tbody tr').length === 0){
                                location.reload(); // Reload to show empty state message
                            }
                        });
                    }
                    
                    if(typeof onSuccess === 'function') onSuccess(response);
                } else {
                    showToast(response.message || 'Operation failed', 'error');
                }
            },
            error: function(xhr, status, error){
                $('#confirmDeleteBtn').html('Delete Plan').prop('disabled', false);
                
                let errorMsg = 'An error occurred. Please try again.';
                if(xhr.responseJSON && xhr.responseJSON.message){
                    errorMsg = xhr.responseJSON.message;
                }
                showToast(errorMsg, 'error');
                console.error('Delete error:', error);
            }
        });
    }

    $(document).ready(function(){
        const config = window.SUBS_PLAN_CONFIG || {};

        // Show toast for created/updated/deleted via server flags
        try{
            if(config.created) showToast('Subscription plan created successfully', 'success');
            if(config.updated) showToast('Subscription plan updated successfully', 'success');
            if(config.deleted) showToast('Subscription plan deleted successfully', 'success');
        } catch(e) {
            console.warn('Toast initialization error:', e);
        }

        // View details - Modal handling
        $(document).on('click', '.view-plan', function(e){
            e.preventDefault();
            const el = $(this);
            
            // Populate modal fields with formatted currency
            $('#detailName').text(el.data('plan-name'));
            $('#detailRole').text(el.data('plan-role'));
            
            // Format monthly price
            const monthlyPrice = el.data('plan-monthly') || 0;
            $('#detailMonthly').text(formatCurrency(monthlyPrice));
            
            // Format half-yearly discount
            const halfDiscount = el.data('plan-half-discount') || 0;
            $('#detailHalfDiscount').text(formatCurrency(halfDiscount));
            
            // Format yearly discount
            const yearDiscount = el.data('plan-year-discount') || 0;
            $('#detailYearDiscount').text(formatCurrency(yearDiscount));
            
            // Handle banking name
            const bankingName = el.data('plan-banking') || 'Not specified';
            $('#detailBanking').text(bankingName);
            
            // Handle description (with line breaks)
            let description = el.data('plan-description') || 'No description provided';
            $('#detailDescription').html(description.replace(/\n/g, '<br>'));
            
            // Handle QR image
            const qrUrl = el.data('plan-qr-url');
            if(qrUrl && qrUrl.trim() !== ''){
                $('#detailQr').attr('src', qrUrl).show();
                $('#noQrMessage').hide();
            } else {
                $('#detailQr').hide();
                $('#noQrMessage').show();
            }

            // Show modal
            const modalEl = document.getElementById('planDetailModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        });

        // Delete flow
        let currentDeleteId = null;
        
        $(document).on('click', '.delete-plan', function(e){
            e.preventDefault();
            currentDeleteId = $(this).data('plan-id');
            
            // Reset delete button state
            $('#confirmDeleteBtn').html('Delete Plan').prop('disabled', false);
            
            // Show confirmation modal
            const modalEl = document.getElementById('confirmDeleteModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        });

        // Handle confirm delete button click
        $(document).on('click', '#confirmDeleteBtn', function(){
            if(!currentDeleteId) {
                showToast('No plan selected for deletion', 'error');
                return;
            }
            
            performDelete(currentDeleteId, config);
        });
        
        // Reset currentDeleteId when delete modal is hidden
        $('#confirmDeleteModal').on('hidden.bs.modal', function(){
            currentDeleteId = null;
        });
    });

})(jQuery);