/**
 * Create Chatbot Form JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Form navigation
    setupFormNavigation();
    
    // Form submission
    setupFormSubmission();
    
    // Preview updates
    setupPreviewUpdates();
    
    // Setup LLM provider and model selection
    setupLLMSelection();
});

function setupFormNavigation() {
    // Next step buttons
    document.querySelectorAll('.next-step').forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = parseInt(this.closest('.form-step').dataset.step);
            const nextStep = currentStep + 1;
            
            if (validateStep(currentStep)) {
                // Hide current step
                document.querySelector(`.form-step[data-step="${currentStep}"]`).classList.add('d-none');
                
                // Show next step
                document.querySelector(`.form-step[data-step="${nextStep}"]`).classList.remove('d-none');
                
                // Update progress indicator
                updateProgressIndicator(nextStep);
                
                // If it's the review step, populate review data
                if (nextStep === 4) {
                    populateReviewData();
                }
            }
        });
    });
    
    // Previous step buttons
    document.querySelectorAll('.prev-step').forEach(button => {
        button.addEventListener('click', function() {
            const currentStep = parseInt(this.closest('.form-step').dataset.step);
            const prevStep = currentStep - 1;
            
            // Hide current step
            document.querySelector(`.form-step[data-step="${currentStep}"]`).classList.add('d-none');
            
            // Show previous step
            document.querySelector(`.form-step[data-step="${prevStep}"]`).classList.remove('d-none');
            
            // Update progress indicator
            updateProgressIndicator(prevStep);
        });
    });
}

function updateProgressIndicator(activeStep) {
    // Remove active class from all steps
    document.querySelectorAll('.progress-step').forEach(step => {
        step.classList.remove('active');
        step.classList.remove('completed');
    });
    
    // Add appropriate classes for each step
    for (let i = 1; i <= 4; i++) {
        const stepEl = document.querySelector(`.progress-step[data-step="${i}"]`);
        if (i < activeStep) {
            stepEl.classList.add('completed');
        } else if (i === activeStep) {
            stepEl.classList.add('active');
        }
    }
}

function validateStep(step) {
    // Basic validation for each step
    switch(step) {
        case 1:
            // Name is required
            const name = document.getElementById('chatbot_name').value;
            if (!name.trim()) {
                alert('Please provide a name for your chatbot.');
                return false;
            }
            return true;
            
        case 2:
            // Provider and model are required
            const provider = document.getElementById('llm_provider').value;
            const model = document.getElementById('llm_model').value;
            if (!provider || !model) {
                alert('Please select an LLM provider and model.');
                return false;
            }
            return true;
            
        default:
            return true;
    }
}

function setupChannelCheckboxes() {
    // Channel checkboxes have been removed
    // This function is kept as a placeholder for backward compatibility
    console.log('Channel configuration has been moved to the chatbot detail page');
}

function populateReviewData() {
    // Basic info
    document.getElementById('review-name').textContent = document.getElementById('chatbot_name').value || 'My Chatbot';
    document.getElementById('review-description').textContent = document.getElementById('chatbot_description').value || 'A helpful AI assistant';
    
    // AI Settings
    const provider = document.getElementById('llm_provider');
    const model = document.getElementById('llm_model');
    document.getElementById('review-provider').textContent = provider.options[provider.selectedIndex]?.text || 'Not selected';
    document.getElementById('review-model').textContent = model.options[model.selectedIndex]?.text || 'Not selected';
    
    // Add prompt to review (truncated if too long)
    const promptText = document.getElementById('chatbot_prompt').value;
    if (document.getElementById('review-prompt')) {
        document.getElementById('review-prompt').textContent = promptText ? 
            (promptText.length > 100 ? promptText.substring(0, 100) + '...' : promptText) : 
            'No custom prompt provided';
    }
    
    // Set default web channel in review
    const channelsContainer = document.getElementById('review-channels');
    if (channelsContainer) {
        channelsContainer.innerHTML = '<div class="review-channel"><i class="bi bi-globe"></i> Web Chat (Default)</div>';
    }
}

function setupFormSubmission() {
    const form = document.getElementById('createChatbotForm');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading state
        const submitButton = this.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
        
        // Gather data
        const formData = new FormData(this);
        const chatbotData = gatherFormData(formData);
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Send AJAX request
        fetch('/chat/add-chatbot/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(chatbotData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Check for success
            if (data.success) {
                // Success - redirect to chatbot dashboard or detail page
                window.location.href = `/chat/chatbot/${data.chatbot}/`;
            } else {
                // Server returned an error
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error creating your chatbot: ' + error.message);
            
            // Reset button
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        });
    });
}

function gatherFormData(formData) {
    // Basic info
    const chatbotData = {
        name: formData.get('name'),
        description: formData.get('description'),
        prompt: formData.get('prompt'),
        llm_provider: formData.get('llm_provider'),
        llm_model: formData.get('llm_model'),
        // Add default web channel
        channels: [{
            type: 'web'
        }]
    };
    
    return chatbotData;
}

function setupPreviewUpdates() {
    // Update preview when name changes
    document.getElementById('chatbot_name').addEventListener('input', function() {
        document.querySelector('.preview-name').textContent = this.value || 'My Chatbot';
    });
    
    // Update preview when avatar changes
    document.getElementById('avatar_upload').addEventListener('change', function(e) {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const previewAvatar = document.querySelector('.preview-avatar img');
                previewAvatar.src = e.target.result;
                previewAvatar.style.display = 'block';
                document.querySelector('.preview-avatar-text').style.display = 'none';
                
                // Also update the main avatar preview
                const avatarPreview = document.querySelector('.avatar-preview img');
                avatarPreview.src = e.target.result;
                avatarPreview.style.display = 'block';
                document.querySelector('.avatar-preview-image').style.display = 'none';
            };
            reader.readAsDataURL(this.files[0]);
        }
    });
    
    // Generate avatar button
    document.querySelector('.generate-avatar-btn').addEventListener('click', function() {
        // In a real implementation, this would call an API to generate an avatar
        alert('Avatar generation would be implemented here. For now, please upload an image.');
    });
}

function setupLLMSelection() {
    const providerSelect = document.getElementById('llm_provider');
    const modelSelect = document.getElementById('llm_model');
    
    // When provider changes, update available models
    providerSelect.addEventListener('change', function() {
        const provider = this.value;
        
        // Clear current options
        modelSelect.innerHTML = '';
        modelSelect.disabled = false;
        
        // Add appropriate options based on provider
        if (provider === 'openai') {
            addModelOption(modelSelect, 'gpt-4o-mini', 'GPT-4o Mini');
            addModelOption(modelSelect, 'gpt-4o', 'GPT-4o');
            addModelOption(modelSelect, 'gpt-4', 'GPT-4');
            addModelOption(modelSelect, 'gpt-3.5-turbo', 'GPT-3.5 Turbo');
        } else if (provider === 'google') {
            addModelOption(modelSelect, 'gemini-1.5-pro-latest', 'Gemini 1.5 Pro');
        } else if (provider === 'deepseek') {
            addModelOption(modelSelect, 'deepseek-chat', 'DeepSeek Chat');
        } else {
            // Add a placeholder if no provider selected
            const option = document.createElement('option');
            option.value = '';
            option.text = 'Select a provider first';
            option.disabled = true;
            option.selected = true;
            modelSelect.appendChild(option);
            modelSelect.disabled = true;
        }
        // Enable the model select
        modelSelect.disabled = false;
    });
    
    function addModelOption(selectElement, value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.text = text;
        selectElement.appendChild(option);
    }
}

function setupGmailConnection() {
    // Gmail connection has been moved to the chatbot detail page
    console.log('Gmail connection setup has been moved to the chatbot detail page');
} 