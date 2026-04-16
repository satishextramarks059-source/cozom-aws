// send_mail_reply.js
// Handles Quill initialization, attachment preview, and AJAX reply submission

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Quill editor
    const quill = new Quill('#editor', {
        theme: 'snow',
        placeholder: 'Type your reply message here...',
        modules: {
            toolbar: [
                [{ header: [1, 2, false] }],
                ['bold', 'italic', 'underline'],
                [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                ['link', 'clean']
            ]
        }
    });

    const form = document.getElementById('replyForm');
    const sendButton = document.getElementById('sendButton');
    const cancelButton = document.getElementById('cancelButton');
    const attachmentInput = document.getElementById('attachment');
    const previewContainer = document.getElementById('attachmentPreview');

    // Attachment preview helper
    function clearPreview(){
        if(previewContainer) previewContainer.innerHTML = '';
    }

    function showFilePreview(file){
        if(!previewContainer) return;
        clearPreview();
        const fileName = file.name;
        const lower = fileName.toLowerCase();

        if(file.type.startsWith('image/') || lower.match(/\.(png|jpg|jpeg|gif)$/)){
            const reader = new FileReader();
            reader.onload = function(e){
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '150px';
                img.style.maxHeight = '150px';
                img.className = 'img-thumbnail';
                previewContainer.appendChild(img);
            };
            reader.readAsDataURL(file);
            return;
        }

        // Non-image types: show icon + filename
        const ext = lower.split('.').pop();
        let iconClass = 'fas fa-file';
        if(ext === 'pdf') iconClass = 'fas fa-file-pdf text-danger';
        else if(ext === 'doc' || ext === 'docx') iconClass = 'fas fa-file-word text-primary';
        else if(ext === 'xls' || ext === 'xlsx' || ext === 'csv') iconClass = 'fas fa-file-excel text-success';

        const wrapper = document.createElement('div');
        wrapper.className = 'd-flex align-items-center gap-2';
        wrapper.innerHTML = `<i class="${iconClass} fa-2x"></i><div>${fileName}</div>`;
        previewContainer.appendChild(wrapper);
    }

    if(attachmentInput){
        attachmentInput.addEventListener('change', function(){
            const file = this.files && this.files[0];
            if(file){
                showFilePreview(file);
            } else {
                clearPreview();
            }
        });
    }

    // Prevent cancel navigation while sending
    function disableCancel(){
        if(cancelButton){
            cancelButton.classList.add('disabled');
            cancelButton.setAttribute('aria-disabled','true');
            cancelButton.addEventListener('click', preventNav);
        }
    }

    function enableCancel(){
        if(cancelButton){
            cancelButton.classList.remove('disabled');
            cancelButton.removeAttribute('aria-disabled');
            cancelButton.removeEventListener('click', preventNav);
        }
    }

    function preventNav(e){
        e.preventDefault();
    }

    // Handle form submit via AJAX
    if(form){
        form.addEventListener('submit', function(e){
            e.preventDefault();

            // Capture Quill content
            const hiddenInput = document.getElementById('message');
            hiddenInput.value = quill.root.innerHTML;

            // Disable buttons
            sendButton.disabled = true;
            const originalHtml = sendButton.innerHTML;
            sendButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
            disableCancel();

            const formData = new FormData(form);

            $.ajax({
                type: 'POST',
                url: window.location.href,
                data: formData,
                processData: false,
                contentType: false,
                success: function(response){
                    if(response.status === 'success'){
                        const successModal = new bootstrap.Modal(document.getElementById('successModal'));
                        successModal.show();
                    } else {
                        alert('Error: ' + response.message);
                        sendButton.disabled = false;
                        sendButton.innerHTML = originalHtml;
                        enableCancel();
                    }
                },
                error: function(){
                    alert('An error occurred while sending the reply. Please try again.');
                    sendButton.disabled = false;
                    sendButton.innerHTML = originalHtml;
                    enableCancel();
                }
            });
        });
    }

});
