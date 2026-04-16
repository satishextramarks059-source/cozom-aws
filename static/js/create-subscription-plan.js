(function(){
    document.addEventListener('DOMContentLoaded', function(){
        const fileInput = document.querySelector('#id_receiver_qr');
        const preview = document.querySelector('#qrPreview');

        function showPreview(file){
            if(!preview) return;
            const url = URL.createObjectURL(file);
            preview.src = url;
            preview.style.display = 'block';
        }

        if(fileInput){
            fileInput.addEventListener('change', function(e){
                const file = e.target.files[0];
                if(!file){
                    // clear preview and validity
                    if(preview){ preview.style.display = 'none'; }
                    fileInput.setCustomValidity('');
                    return;
                }
                const validTypes = ['image/png','image/jpeg','image/jpg'];
                if(!validTypes.includes(file.type)){
                    // use HTML5 validation messaging instead of alert
                    fileInput.setCustomValidity('Invalid file type. Only PNG/JPG/JPEG allowed.');
                    fileInput.reportValidity();
                    fileInput.value = '';
                    if(preview){ preview.style.display='none'; }
                    return;
                }
                // clear any previous custom validity
                fileInput.setCustomValidity('');
                showPreview(file);
            });
        }

        // Log form submit for debugging (does not prevent submission)
        const form = document.getElementById('subscriptionPlanForm');
        if(form){
            form.addEventListener('submit', function(e){
                try{
                    console.info('Submitting subscription plan form');
                    const fd = new FormData(form);
                    for (let pair of fd.entries()){
                        console.info('formdata', pair[0], pair[1]);
                    }
                } catch(err){
                    console.error('Error logging form data', err);
                }
            });
        }
    });
})();
