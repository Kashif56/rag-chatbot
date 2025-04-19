document.addEventListener('DOMContentLoaded', function() {
    // Make cards clickable - new functionality
    const datasourceCards = document.querySelectorAll('.datasource-card');
    datasourceCards.forEach(card => {
        // Make the whole card clickable except for the delete button
        card.addEventListener('click', function(e) {
            // Don't trigger card click if user clicked the delete button or any links
            if (e.target.closest('.delete-source-btn') || e.target.tagName === 'A' || e.target.closest('a')) {
                return;
            }
            
            // Get source ID from the data attribute or nearest delete button
            const sourceId = this.getAttribute('data-source-id') || 
                             this.querySelector('.delete-source-btn')?.getAttribute('data-source-id');
            
            if (sourceId) {
                window.location.href = `/kb/source/${sourceId}/`;
            }
        });
        
        // Add pointer cursor to indicate clickable
        card.style.cursor = 'pointer';
    });
    
    // Source type selection
    const sourceTypeInputs = document.querySelectorAll('.source-type-input');
    const formSections = document.querySelectorAll('.form-section');
    const sourceTypeCards = document.querySelectorAll('.source-type-card');
    
    sourceTypeInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Update selected card styling
            sourceTypeCards.forEach(card => {
                card.classList.remove('selected');
            });
            this.closest('.source-type-card').classList.add('selected');
            
            // Show the appropriate form section
            formSections.forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(`${this.value}_section`).classList.add('active');
        });
    });
    
    // Search functionality
    const searchInput = document.getElementById('datasource-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const sourceCards = document.querySelectorAll('.datasource-card');
            
            sourceCards.forEach(card => {
                const title = card.querySelector('.datasource-title').textContent.toLowerCase();
                const content = card.querySelector('.datasource-content').textContent.toLowerCase();
                const isVisible = title.includes(searchTerm) || content.includes(searchTerm);
                
                card.style.display = isVisible ? 'flex' : 'none';
            });
        });
    }
    
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-buttons button');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active button
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            const filter = this.getAttribute('data-filter');
            const sourceCards = document.querySelectorAll('.datasource-card');
            
            sourceCards.forEach(card => {
                if (filter === 'all' || card.getAttribute('data-source-type') === filter) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });
    
    // Form submission
    const submitBtn = document.getElementById('submitDataSourceBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            const form = document.getElementById('addDataSourceForm');
            const sourceType = document.querySelector('input[name="source_type"]:checked');
            const modalBody = document.querySelector('#addDataSourceModal .modal-body');
            
            if (!sourceType) {
                alert('Please select a source type');
                return;
            }
            
            // Add the form action dynamically based on the KB ID
            const kbId = document.querySelector('input[name="kb_id"]').value;
            form.action = `/kb/add-source/${kbId}/`;
            
            // Form validation based on selected type
            let isValid = true;
            
            switch (sourceType.value) {
                case 'file':
                    const fileTitle = document.getElementById('file_title');
                    const fileUpload = document.getElementById('file_upload');
                    
                    if (!fileTitle.value.trim()) {
                        alert('Please enter a title for your file');
                        isValid = false;
                    } else if (!fileUpload.files || fileUpload.files.length === 0) {
                        alert('Please select a file to upload');
                        isValid = false;
                    }
                    break;
                    
                case 'url':
                    const urlTitle = document.getElementById('url_title');
                    const urlInput = document.getElementById('url_input');
                    
                    if (!urlTitle.value.trim()) {
                        alert('Please enter a title for your URL');
                        isValid = false;
                    } else if (!urlInput.value.trim() || !urlInput.validity.valid) {
                        alert('Please enter a valid URL');
                        isValid = false;
                    }
                    break;
                    
                case 'text':
                    const textTitle = document.getElementById('text_title');
                    const textContent = document.getElementById('text_content');
                    
                    if (!textTitle.value.trim()) {
                        alert('Please enter a title for your text');
                        isValid = false;
                    } else if (!textContent.value.trim()) {
                        alert('Please enter some content for your text');
                        isValid = false;
                    }
                    break;
            }
            
            if (isValid) {
                // Disable the submit button to prevent double clicks
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                // Create loader overlay
                const loaderHTML = `
                    <div class="processing-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.8); display: flex; justify-content: center; align-items: center; z-index: 10;">
                        <div class="text-center">
                            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <h5 class="mb-1">Processing Data Source</h5>
                            <p class="text-muted mb-0 small">This may take a moment depending on the file size or content length.</p>
                        </div>
                    </div>
                `;
                
                // Add the loader to the modal
                modalBody.style.position = 'relative';
                modalBody.insertAdjacentHTML('beforeend', loaderHTML);
                
                // Use AJAX to submit the form
                const formData = new FormData(form);
                
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    // Remove loader
                    const overlay = document.querySelector('.processing-overlay');
                    if (overlay) overlay.remove();
                    
                    if (data.status === 'success') {
                        // Success - reload the page or show success message
                        window.location.reload();
                    } else {
                        // Error handling
                        alert(data.error || 'There was an error processing your data source.');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = 'Add Data Source';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('There was an error processing your request. Please try again.');
                    
                    // Remove loader and reset button
                    const overlay = document.querySelector('.processing-overlay');
                    if (overlay) overlay.remove();
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Add Data Source';
                });
            }
        });
    }
    
    // Delete source modal
    const deleteSourceModal = document.getElementById('deleteSourceModal');
    if (deleteSourceModal) {
        deleteSourceModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const sourceId = button.getAttribute('data-source-id');
            const sourceTitle = button.getAttribute('data-source-title');
            
            document.getElementById('delete-source-title').textContent = sourceTitle;
            document.getElementById('delete_source_id').value = sourceId;
        });
        
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', function() {
                const form = document.getElementById('deleteDataSourceForm');
                const sourceId = document.getElementById('delete_source_id').value;
                const modalBody = document.querySelector('#deleteSourceModal .modal-body');
                
                // Disable the delete button to prevent double clicks
                confirmDeleteBtn.disabled = true;
                confirmDeleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';
                
                // Create loader overlay
                const loaderHTML = `
                    <div class="processing-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.8); display: flex; justify-content: center; align-items: center; z-index: 10;">
                        <div class="text-center">
                            <div class="spinner-border text-danger mb-3" role="status" style="width: 3rem; height: 3rem;">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <h5 class="mb-1">Deleting Data Source</h5>
                            <p class="text-muted mb-0 small">This may take a moment...</p>
                        </div>
                    </div>
                `;
                
                // Add the loader to the modal
                modalBody.style.position = 'relative';
                modalBody.insertAdjacentHTML('beforeend', loaderHTML);
                
                // Get CSRF token from the form
                const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]').value;
                
                fetch(`/kb/delete-source/${sourceId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Success - show a brief success message before redirecting
                        const overlay = document.querySelector('#deleteSourceModal .processing-overlay');
                        if (overlay) {
                            overlay.innerHTML = `
                                <div class="text-center">
                                    <div class="text-success mb-3">
                                        <i class="fas fa-check-circle" style="font-size: 3rem;"></i>
                                    </div>
                                    <h5 class="mb-1">Successfully Deleted!</h5>
                                </div>
                            `;
                            
                            // Redirect after a short delay to show the success message
                            setTimeout(() => {
                                window.location.href = data.redirect_url || window.location.href;
                            }, 800);
                        } else {
                            window.location.href = data.redirect_url || window.location.href;
                        }
                    } else {
                        // Error handling
                        alert(data.error || 'There was an error deleting the data source.');
                        
                        // Remove loader and reset button
                        const overlay = document.querySelector('#deleteSourceModal .processing-overlay');
                        if (overlay) overlay.remove();
                        confirmDeleteBtn.disabled = false;
                        confirmDeleteBtn.innerHTML = 'Delete';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('There was an error processing your request. Please try again.');
                    
                    // Remove loader and reset button
                    const overlay = document.querySelector('#deleteSourceModal .processing-overlay');
                    if (overlay) overlay.remove();
                    confirmDeleteBtn.disabled = false;
                    confirmDeleteBtn.innerHTML = 'Delete';
                });
            });
        }
    }

    // File upload preview
    const fileUpload = document.getElementById('file_upload');
    if (fileUpload) {
        fileUpload.addEventListener('change', function() {
            const fileNameElement = document.querySelector('.file-name');
            if (this.files.length > 0) {
                const fileName = this.files[0].name;
                const fileSize = (this.files[0].size / 1024).toFixed(2) + ' KB';
                
                if (!fileNameElement) {
                    const fileInfoDiv = document.createElement('div');
                    fileInfoDiv.className = 'file-info mt-2 p-2 bg-light rounded';
                    fileInfoDiv.innerHTML = `
                        <div class="d-flex align-items-center">
                            <i class="fas fa-file me-2 text-primary"></i>
                            <div>
                                <div class="file-name fw-bold">${fileName}</div>
                                <div class="file-size text-muted small">${fileSize}</div>
                            </div>
                        </div>
                    `;
                    
                    this.parentElement.appendChild(fileInfoDiv);
                } else {
                    fileNameElement.textContent = fileName;
                    fileNameElement.nextElementSibling.textContent = fileSize;
                }
            }
        });
    }

    // URL validation with visual feedback
    const urlInput = document.getElementById('url_input');
    if (urlInput) {
        urlInput.addEventListener('input', function() {
            validateUrl(this);
        });
        
        urlInput.addEventListener('blur', function() {
            validateUrl(this, true);
        });
    }

    function validateUrl(inputElement, showError = false) {
        const urlPattern = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
        const isValid = urlPattern.test(inputElement.value);
        
        if (inputElement.value) {
            if (isValid) {
                inputElement.classList.remove('is-invalid');
                inputElement.classList.add('is-valid');
                
                const feedbackElement = inputElement.parentElement.querySelector('.invalid-feedback');
                if (feedbackElement) {
                    feedbackElement.remove();
                }
            } else if (showError) {
                inputElement.classList.remove('is-valid');
                inputElement.classList.add('is-invalid');
                
                if (!inputElement.parentElement.querySelector('.invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Please enter a valid URL (e.g., https://example.com)';
                    inputElement.parentElement.appendChild(feedback);
                }
            }
        } else {
            inputElement.classList.remove('is-valid', 'is-invalid');
            
            const feedbackElement = inputElement.parentElement.querySelector('.invalid-feedback');
            if (feedbackElement) {
                feedbackElement.remove();
            }
        }
    }

    // Text counter for text content
    const textContent = document.getElementById('text_content');
    if (textContent) {
        textContent.addEventListener('input', function() {
            updateCharCount(this);
        });
        
        // Initialize counter
        if (!textContent.parentElement.querySelector('.char-counter')) {
            const counterDiv = document.createElement('div');
            counterDiv.className = 'char-counter text-muted text-end small mt-1';
            textContent.parentElement.appendChild(counterDiv);
            updateCharCount(textContent);
        }
    }

    function updateCharCount(textarea) {
        const counter = textarea.parentElement.querySelector('.char-counter');
        const charCount = textarea.value.length;
        counter.textContent = `${charCount} characters`;
        
        if (charCount > 5000) {
            counter.classList.add('text-danger');
        } else {
            counter.classList.remove('text-danger');
        }
    }

    // Handle follow_links checkbox toggling max_depth_container visibility
    const followLinksCheckbox = document.getElementById('follow_links');
    const maxDepthContainer = document.getElementById('max_depth_container');
    
    if (followLinksCheckbox && maxDepthContainer) {
        followLinksCheckbox.addEventListener('change', function() {
            maxDepthContainer.style.display = this.checked ? 'block' : 'none';
        });
    }

    // Initialize the first source type option
    if (sourceTypeCards.length > 0 && !document.querySelector('.source-type-card.selected')) {
        sourceTypeCards[0].click();
    }
}); 