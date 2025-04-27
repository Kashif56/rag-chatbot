/**
 * Create Chatbot Form JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Form navigation
    setupFormNavigation();
    
    // Channel checkbox handling
    setupChannelCheckboxes();
    
    // Form submission
    setupFormSubmission();
    
    // Preview updates
    setupPreviewUpdates();
    
    // Setup LLM provider and model selection
    setupLLMSelection();
    
    // Setup Gmail connection button
    setupGmailConnection();
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
            
        case 3:
            // At least one channel must be selected
            const channels = document.querySelectorAll('.channel-checkbox:checked');
            if (channels.length === 0) {
                alert('Please select at least one channel.');
                return false;
            }
            return true;
            
        default:
            return true;
    }
}

function setupChannelCheckboxes() {
    const channelCheckboxes = document.querySelectorAll('.channel-checkbox');
    
    channelCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const channelType = this.value;
            const configForm = document.getElementById(`${channelType}_config`);
            
            if (this.checked) {
                configForm.classList.remove('d-none');
            } else {
                configForm.classList.add('d-none');
            }
            
            // Special handling for WhatsApp and SMS since they share Twilio config
            handleSharedTwilioConfig();
        });
    });
}

function handleSharedTwilioConfig() {
    const whatsappEnabled = document.getElementById('channel_whatsapp').checked;
    const smsEnabled = document.getElementById('channel_sms').checked;
    
    const whatsappSmsInfo = document.getElementById('whatsapp_sms_shared_info');
    const smsWhatsappInfo = document.getElementById('sms_whatsapp_shared_info');
    const whatsappFields = document.getElementById('whatsapp_twilio_fields');
    const smsFields = document.getElementById('sms_twilio_fields');
    
    if (whatsappEnabled && smsEnabled) {
        // Show message in SMS config that we're using WhatsApp's Twilio config
        smsWhatsappInfo.classList.remove('d-none');
        smsFields.classList.add('d-none');
        
        // Hide message in WhatsApp config
        whatsappSmsInfo.classList.add('d-none');
        whatsappFields.classList.remove('d-none');
    } else {
        // Reset to default views
        smsWhatsappInfo.classList.add('d-none');
        smsFields.classList.remove('d-none');
        whatsappSmsInfo.classList.add('d-none');
        whatsappFields.classList.remove('d-none');
    }
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
    
    // Channels
    const channelsContainer = document.getElementById('review-channels');
    channelsContainer.innerHTML = '';
    
    document.querySelectorAll('.channel-checkbox:checked').forEach(channel => {
        const channelType = channel.value;
        const channelName = channel.nextElementSibling.querySelector('.channel-name').textContent;
        
        const channelDiv = document.createElement('div');
        channelDiv.className = 'review-channel';
        
        let icon;
        switch(channelType) {
            case 'web': icon = 'bi-globe'; break;
            case 'whatsapp': icon = 'bi-whatsapp'; break;
            case 'messenger': icon = 'bi-messenger'; break;
            case 'sms': icon = 'bi-chat-dots'; break;
            case 'email': icon = 'bi-envelope'; break;
            default: icon = 'bi-chat'; break;
        }
        
        channelDiv.innerHTML = `<i class="bi ${icon}"></i> ${channelName}`;
        channelsContainer.appendChild(channelDiv);
    });
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
        channels: []
    };
    
    // Get selected channels and their configs
    const selectedChannels = document.querySelectorAll('.channel-checkbox:checked');
    selectedChannels.forEach(channelCheckbox => {
        const channelType = channelCheckbox.value;
        let channelConfig = {
            type: channelType
        };
        
        // Add channel-specific configurations
        switch(channelType) {
            case 'whatsapp':
                // Check if we should use SMS config instead (if both are enabled)
                if (document.getElementById('channel_sms').checked) {
                    channelConfig = {
                        ...channelConfig,
                        twilio_account_sid: formData.get('sms_twilio_account_sid'),
                        twilio_auth_token: formData.get('sms_twilio_auth_token'),
                        twilio_phone_number: formData.get('sms_twilio_phone_number')
                    };
                } else {
                    channelConfig = {
                        ...channelConfig,
                        twilio_account_sid: formData.get('twilio_account_sid'),
                        twilio_auth_token: formData.get('twilio_auth_token'),
                        twilio_phone_number: formData.get('twilio_phone_number')
                    };
                }
                break;
            
            case 'sms':
                // Check if we should use WhatsApp config instead (if both are enabled)
                if (document.getElementById('channel_whatsapp').checked) {
                    channelConfig = {
                        ...channelConfig,
                        twilio_account_sid: formData.get('twilio_account_sid'),
                        twilio_auth_token: formData.get('twilio_auth_token'),
                        twilio_phone_number: formData.get('twilio_phone_number')
                    };
                } else {
                    channelConfig = {
                        ...channelConfig,
                        twilio_account_sid: formData.get('sms_twilio_account_sid'),
                        twilio_auth_token: formData.get('sms_twilio_auth_token'),
                        twilio_phone_number: formData.get('sms_twilio_phone_number')
                    };
                }
                break;
            
            case 'messenger':
                channelConfig = {
                    ...channelConfig,
                    page_id: formData.get('page_id'),
                    page_name: formData.get('page_name'),
                    access_token: formData.get('messenger_access_token')
                };
                break;
            
            case 'email':
                channelConfig = {
                    ...channelConfig,
                    email_address: formData.get('email_address'),
                    provider: formData.get('email_provider'),
                    access_token: formData.get('email_access_token'),
                    refresh_token: '',  // Add if you have this field
                    smtp_server: formData.get('smtp_server') || '',
                    smtp_port: formData.get('smtp_port') || '',
                    imap_server: formData.get('imap_server') || ''
                };
                break;
            
            case 'web':
                // No additional config needed for web channel
                break;
        }
        
        chatbotData.channels.push(channelConfig);
    });
    
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
    // Get the email provider select element
    const emailProviderSelect = document.getElementById('email_provider');
    let gmailAuthSection = document.getElementById('gmail_auth_section');
    const emailTokenSection = document.getElementById('email_token_section');
    const connectGmailBtn = document.getElementById('connect_gmail_btn');
    
    // Check if we're on the edit page or create page
    const isEditPage = window.location.pathname.includes('/chatbot/');
    const isCreatePage = window.location.pathname.includes('/create-chatbot/');
    
    // Show/hide Gmail auth section based on provider selection
    if (emailProviderSelect) {
        emailProviderSelect.addEventListener('change', function() {
            const provider = this.value;
            
            if (provider === 'gmail') {
                // Show Gmail auth section and hide token input
                gmailAuthSection.classList.remove('d-none');
                emailTokenSection.classList.add('d-none');
                console.log('Gmail Auth Section display:', gmailAuthSection.className);
                console.log("Email Token Section display:", emailTokenSection.className);
            } else {
                // Hide Gmail auth section and show token input
                gmailAuthSection.classList.add('d-none');
                emailTokenSection.classList.remove('d-none');
            }
        });
    }
    
    // Handle Gmail connect button click
    if (connectGmailBtn) {
        connectGmailBtn.addEventListener('click', function() {
            // If we're on the create page, we need to save the chatbot first
            if (isCreatePage) {
                alert('Please save the chatbot first before connecting Gmail.');
                return;
            }
            
            // Get the chatbot_id from the URL
            const urlParams = new URLSearchParams(window.location.search);
            let chatbotId = urlParams.get('chatbot_id');
            
            // If no chatbot_id in URL, try to extract it from the pathname
            if (!chatbotId) {
                const pathParts = window.location.pathname.split('/');
                for (const part of pathParts) {
                    if (part.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)) {
                        chatbotId = part;
                        break;
                    }
                }
            }
            
            if (!chatbotId) {
                alert('Could not find chatbot ID. Please reload the page or try again.');
                return;
            }
            
            // We need to create the channel first to get a channel_id
            // This will be a temporary channel that will be updated after OAuth
            const formData = new FormData();
            formData.append('channel_type', 'email');
            formData.append('email_address', document.getElementById('email_address').value || '');
            formData.append('email_provider', 'gmail');
            
            // Create a temporary channel to get a channel_id
            fetch(`/chat/add-channel/${chatbotId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.channel_id) {
                    // Redirect to Gmail auth endpoint with the channel_id
                    window.location.href = `/chat/google/auth/${data.channel_id}/`;
                } else {
                    alert('Failed to create email channel. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while connecting to Gmail. Please try again.');
            });
        });
    }
} 