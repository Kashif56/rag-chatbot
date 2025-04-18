/**
 * Create Chatbot Form JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const nextButtons = document.querySelectorAll('.next-step');
    const prevButtons = document.querySelectorAll('.prev-step');
    const formSteps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.progress-step');
    const progressLines = document.querySelectorAll('.progress-line');
    const llmProviderSelect = document.getElementById('llm_provider');
    const llmModelSelect = document.getElementById('llm_model');
    const chatbotNameInput = document.getElementById('chatbot_name');
    const chatbotDescriptionInput = document.getElementById('chatbot_description');
    const previewNameElement = document.querySelector('.preview-name');
    const previewAvatarText = document.querySelector('.preview-avatar-text');
    const previewBubble = document.querySelector('.preview-bubble');
    const avatarUpload = document.getElementById('avatar_upload');
    const avatarPreviewImg = document.querySelector('.avatar-preview img');
    const generateAvatarBtn = document.querySelector('.generate-avatar-btn');
    const knowledgeBaseOnlyCheckbox = document.getElementById('knowledge_base_only');
    const channelCheckboxes = document.querySelectorAll('.channel-checkbox');
    const emailProviderSelect = document.getElementById('email_provider');

    let currentStep = 0;

    // Initialize progress steps
    updateProgressSteps();

    // Handle next button clicks
    nextButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Simple validation (can be expanded)
            if (validateCurrentStep()) {
                if (currentStep < formSteps.length - 1) {
                    formSteps[currentStep].classList.add('d-none');
                    currentStep++;
                    formSteps[currentStep].classList.remove('d-none');
                    updateProgressSteps();
                    
                    // Update review section when going to the review step
                    if (currentStep === 3) { // Review step (0-based index)
                        updateReviewSection();
                    }
                    
                    window.scrollTo(0, 0);
                }
            }
        });
    });

    // Handle previous button clicks
    prevButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentStep > 0) {
                formSteps[currentStep].classList.add('d-none');
                currentStep--;
                formSteps[currentStep].classList.remove('d-none');
                updateProgressSteps();
                window.scrollTo(0, 0);
            }
        });
    });

    // Handle channel checkbox changes
    if (channelCheckboxes) {
        channelCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const channelType = this.value;
                const configForm = document.getElementById(`${channelType}_config`);
                
                if (configForm) {
                    if (this.checked) {
                        configForm.classList.remove('d-none');
                    } else {
                        configForm.classList.add('d-none');
                    }
                }
                
                // Handle special case for SMS and WhatsApp interaction
                updateSmsWhatsappInteraction();
            });
        });
    }

    // Function to update SMS and WhatsApp forms based on their selection
    function updateSmsWhatsappInteraction() {
        const whatsappCheckbox = document.getElementById('channel_whatsapp');
        const smsCheckbox = document.getElementById('channel_sms');
        
        // Only proceed if both checkboxes exist
        if (!whatsappCheckbox || !smsCheckbox) return;
        
        // Elements for SMS configuration
        const smsWhatsappSharedInfo = document.getElementById('sms_whatsapp_shared_info');
        const smsTwilioFields = document.getElementById('sms_twilio_fields');
        
        // Elements for WhatsApp configuration
        const whatsappSmsSharedInfo = document.getElementById('whatsapp_sms_shared_info');
        const whatsappTwilioFields = document.getElementById('whatsapp_twilio_fields');
        
        // First, handle the case where neither is checked
        if (!whatsappCheckbox.checked && !smsCheckbox.checked) {
            // Reset both configurations to show their fields
            if (smsTwilioFields) smsTwilioFields.classList.remove('d-none');
            if (smsWhatsappSharedInfo) smsWhatsappSharedInfo.classList.add('d-none');
            if (whatsappTwilioFields) whatsappTwilioFields.classList.remove('d-none');
            if (whatsappSmsSharedInfo) whatsappSmsSharedInfo.classList.add('d-none');
            return;
        }
        
        // Check if both are checked
        if (whatsappCheckbox.checked && smsCheckbox.checked) {
            // Determine which was checked first (we'll use localStorage to track this)
            const firstSelected = localStorage.getItem('twilio_first_selected');
            
            if (firstSelected === 'sms') {
                // SMS was selected first, so WhatsApp should show the shared message
                if (whatsappSmsSharedInfo) whatsappSmsSharedInfo.classList.remove('d-none');
                if (whatsappTwilioFields) whatsappTwilioFields.classList.add('d-none');
                if (smsTwilioFields) smsTwilioFields.classList.remove('d-none');
                if (smsWhatsappSharedInfo) smsWhatsappSharedInfo.classList.add('d-none');
            } else {
                // WhatsApp was selected first (or no record), so SMS should show the shared message
                if (smsWhatsappSharedInfo) smsWhatsappSharedInfo.classList.remove('d-none');
                if (smsTwilioFields) smsTwilioFields.classList.add('d-none');
                if (whatsappTwilioFields) whatsappTwilioFields.classList.remove('d-none');
                if (whatsappSmsSharedInfo) whatsappSmsSharedInfo.classList.add('d-none');
            }
        } else {
            // Only one is checked, record which one
            if (whatsappCheckbox.checked) {
                localStorage.setItem('twilio_first_selected', 'whatsapp');
                // Ensure WhatsApp shows its fields
                if (whatsappTwilioFields) whatsappTwilioFields.classList.remove('d-none');
                if (whatsappSmsSharedInfo) whatsappSmsSharedInfo.classList.add('d-none');
            } else if (smsCheckbox.checked) {
                localStorage.setItem('twilio_first_selected', 'sms');
                // Ensure SMS shows its fields
                if (smsTwilioFields) smsTwilioFields.classList.remove('d-none');
                if (smsWhatsappSharedInfo) smsWhatsappSharedInfo.classList.add('d-none');
            }
        }
    }
    
    // Watch both checkboxes for changes
    const whatsappCheckbox = document.getElementById('channel_whatsapp');
    const smsCheckbox = document.getElementById('channel_sms');
    
    if (whatsappCheckbox) {
        whatsappCheckbox.addEventListener('change', function() {
            updateSmsWhatsappInteraction();
        });
    }
    
    if (smsCheckbox) {
        smsCheckbox.addEventListener('change', function() {
            updateSmsWhatsappInteraction();
        });
    }
    
    // Initialize SMS/WhatsApp state on page load
    updateSmsWhatsappInteraction();

    // Handle email provider change
    if (emailProviderSelect) {
        emailProviderSelect.addEventListener('change', function() {
            const customEmailSettings = document.getElementById('custom_email_settings');
            if (customEmailSettings) {
                if (this.value === 'imap' || this.value === 'smtp') {
                    customEmailSettings.classList.remove('d-none');
                } else {
                    customEmailSettings.classList.add('d-none');
                }
            }
        });
    }

    // Handle LLM provider change
    if (llmProviderSelect) {
        llmProviderSelect.addEventListener('change', function() {
            updateModelOptions();
        });
        
        // Initialize model options
        updateModelOptions();
    }

    // Update preview when chatbot name changes
    if (chatbotNameInput && previewNameElement) {
        chatbotNameInput.addEventListener('input', function() {
            previewNameElement.textContent = this.value || 'My Chatbot';
            if (previewAvatarText) {
                const initials = getInitials(this.value || 'My Chatbot');
                previewAvatarText.textContent = initials;
            }
        });
    }

    // Update preview when chatbot description changes
    if (chatbotDescriptionInput && previewBubble) {
        chatbotDescriptionInput.addEventListener('input', function() {
            const initialMessage = this.value || 'Hello! How can I help you today?';
            previewBubble.textContent = initialMessage;
        });
    }

    // Handle avatar upload
    if (avatarUpload && avatarPreviewImg) {
        avatarUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    avatarPreviewImg.src = event.target.result;
                    avatarPreviewImg.style.display = 'block';
                    
                    // Also update the preview avatar if it exists
                    const previewAvatar = document.querySelector('.preview-avatar img');
                    if (previewAvatar) {
                        previewAvatar.src = event.target.result;
                        previewAvatar.style.display = 'block';
                        
                        // Hide the avatar text when image is shown
                        if (previewAvatarText) {
                            previewAvatarText.style.display = 'none';
                        }
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Handle generate avatar button
    if (generateAvatarBtn) {
        generateAvatarBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // This would typically call an API to generate an avatar
            // For now, we'll just simulate with a placeholder
            const randomColor = getRandomColor();
            document.querySelector('.avatar-preview').style.backgroundColor = randomColor;
            document.querySelector('.preview-avatar').style.backgroundColor = randomColor;
            
            // Set a placeholder avatar text based on chatbot name
            const name = chatbotNameInput.value || 'My Chatbot';
            const initials = getInitials(name);
            
            if (document.querySelector('.avatar-preview-image')) {
                document.querySelector('.avatar-preview-image').textContent = initials;
            }
            
            if (previewAvatarText) {
                previewAvatarText.style.display = 'flex';
                previewAvatarText.textContent = initials;
            }
            
            // Hide any existing image
            if (avatarPreviewImg) {
                avatarPreviewImg.style.display = 'none';
            }
            
            const previewAvatar = document.querySelector('.preview-avatar img');
            if (previewAvatar) {
                previewAvatar.style.display = 'none';
            }
        });
    }

    // Function to update the review section with current form values
    function updateReviewSection() {
        // Update basic information
        document.getElementById('review-name').textContent = chatbotNameInput.value || 'My Chatbot';
        document.getElementById('review-description').textContent = chatbotDescriptionInput.value || 'A helpful AI assistant';
        
        // Update AI settings
        if (llmProviderSelect && llmProviderSelect.value) {
            const providerText = llmProviderSelect.options[llmProviderSelect.selectedIndex].text;
            document.getElementById('review-provider').textContent = providerText;
        }
        
        if (llmModelSelect && llmModelSelect.value) {
            const modelText = llmModelSelect.options[llmModelSelect.selectedIndex].text;
            document.getElementById('review-model').textContent = modelText;
        }
        
        // Update knowledge base only status
        const kbOnlyElement = document.getElementById('review-kb-only');
        if (kbOnlyElement && knowledgeBaseOnlyCheckbox) {
            kbOnlyElement.innerHTML = knowledgeBaseOnlyCheckbox.checked ? 
                '<span class="badge bg-success">Enabled</span>' : 
                '<span class="badge bg-secondary">Disabled</span>';
        }
        
        // Update show sources status
        const showSourcesElement = document.getElementById('review-sources');
        if (showSourcesElement && showSourcesCheckbox) {
            showSourcesElement.innerHTML = showSourcesCheckbox.checked ? 
                '<span class="badge bg-success">Enabled</span>' : 
                '<span class="badge bg-secondary">Disabled</span>';
        }
        
        // Update selected channels
        const reviewChannelsElement = document.getElementById('review-channels');
        if (reviewChannelsElement) {
            reviewChannelsElement.innerHTML = '';
            
            const selectedChannels = document.querySelectorAll('.channel-checkbox:checked');
            if (selectedChannels.length === 0) {
                reviewChannelsElement.innerHTML = '<div class="text-muted">No channels selected</div>';
            } else {
                selectedChannels.forEach(channel => {
                    const channelValue = channel.value;
                    const channelName = channel.nextElementSibling.querySelector('.channel-name').textContent;
                    const iconElement = channel.nextElementSibling.querySelector('.channel-icon i');
                    const iconClass = iconElement ? iconElement.className : 'bi bi-check';
                    
                    const channelElement = document.createElement('div');
                    channelElement.className = 'review-channel';
                    channelElement.innerHTML = `<i class="${iconClass}"></i> ${channelName}`;
                    
                    // Add channel-specific configuration details
                    if (channelValue === 'email') {
                        const emailAddress = document.getElementById('email_address');
                        const emailProvider = document.getElementById('email_provider');
                        if (emailAddress && emailAddress.value) {
                            const providerValue = emailProvider ? emailProvider.options[emailProvider.selectedIndex].text : '';
                            channelElement.innerHTML += ` <small class="text-muted">(${emailAddress.value}${providerValue ? ' - ' + providerValue : ''})</small>`;
                        }
                    } else if (channelValue === 'whatsapp') {
                        const phoneNumber = document.getElementById('twilio_phone_number');
                        if (phoneNumber && phoneNumber.value) {
                            channelElement.innerHTML += ` <small class="text-muted">(${phoneNumber.value})</small>`;
                        }
                    } else if (channelValue === 'messenger') {
                        const pageName = document.getElementById('page_name');
                        if (pageName && pageName.value) {
                            channelElement.innerHTML += ` <small class="text-muted">(${pageName.value})</small>`;
                        }
                    } else if (channelValue === 'sms') {
                        const smsPhoneNumber = document.getElementById('sms_twilio_phone_number');
                        const whatsappPhoneNumber = document.getElementById('twilio_phone_number');
                        if (smsPhoneNumber && smsPhoneNumber.value) {
                            channelElement.innerHTML += ` <small class="text-muted">(${smsPhoneNumber.value})</small>`;
                        } else if (whatsappPhoneNumber && whatsappPhoneNumber.value) {
                            channelElement.innerHTML += ` <small class="text-muted">(${whatsappPhoneNumber.value})</small>`;
                        }
                    }
                    
                    reviewChannelsElement.appendChild(channelElement);
                });
            }
        }
    }

    // Helper functions
    function updateProgressSteps() {
        progressSteps.forEach((step, index) => {
            if (index < currentStep) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (index === currentStep) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });

        progressLines.forEach((line, index) => {
            if (index < currentStep) {
                line.classList.add('active');
            } else {
                line.classList.remove('active');
            }
        });
    }

    function validateCurrentStep() {
        // Basic validation logic - can be expanded with more detailed validation
        let isValid = true;
        
        // Get all required fields in the current step
        const requiredFields = formSteps[currentStep].querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        // Additional validation for channels step
        if (currentStep === 2) { // Channels step (0-based index)
            // Check if at least one channel is selected
            const selectedChannels = document.querySelectorAll('.channel-checkbox:checked');
            if (selectedChannels.length === 0) {
                const channelAlert = document.querySelector('.channel-info');
                channelAlert.classList.remove('alert-info');
                channelAlert.classList.add('alert-danger');
                channelAlert.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-2"></i><span>Please select at least one channel where users will access your chatbot.</span>';
                isValid = false;
            } else {
                const channelAlert = document.querySelector('.channel-info');
                channelAlert.classList.add('alert-info');
                channelAlert.classList.remove('alert-danger');
                channelAlert.innerHTML = '<i class="bi bi-info-circle-fill me-2"></i><span>Please select at least one channel where users will access your chatbot.</span>';
                
                // Validate each selected channel's configuration
                selectedChannels.forEach(channel => {
                    const channelType = channel.value;
                    const configForm = document.getElementById(`${channelType}_config`);
                    
                    if (configForm) {
                        // Validate required fields for each channel type
                        switch (channelType) {
                            case 'email':
                                const emailAddress = document.getElementById('email_address');
                                const emailProvider = document.getElementById('email_provider');
                                const emailAccessToken = document.getElementById('email_access_token');
                                
                                if (emailAddress && !emailAddress.value.trim()) {
                                    emailAddress.classList.add('is-invalid');
                                    isValid = false;
                                }
                                
                                if (emailProvider && !emailProvider.value) {
                                    emailProvider.classList.add('is-invalid');
                                    isValid = false;
                                }
                                
                                if (emailAccessToken && !emailAccessToken.value.trim()) {
                                    emailAccessToken.classList.add('is-invalid');
                                    isValid = false;
                                }
                                
                                // Validate SMTP/IMAP fields if custom provider selected
                                if (emailProvider && (emailProvider.value === 'imap' || emailProvider.value === 'smtp')) {
                                    const customFields = ['smtp_server', 'smtp_port', 'imap_server', 'imap_port'];
                                    customFields.forEach(fieldId => {
                                        const field = document.getElementById(fieldId);
                                        if (field && !field.value.trim()) {
                                            field.classList.add('is-invalid');
                                            isValid = false;
                                        }
                                    });
                                }
                                break;
                                
                            case 'whatsapp':
                                // Check if SMS is selected first
                                const smsCheckboxForWhatsapp = document.getElementById('channel_sms');
                                const whatsappSmsSharedInfo = document.getElementById('whatsapp_sms_shared_info');
                                
                                // If SMS is selected first, no need to validate WhatsApp fields
                                if (smsCheckboxForWhatsapp && smsCheckboxForWhatsapp.checked && 
                                    whatsappSmsSharedInfo && !whatsappSmsSharedInfo.classList.contains('d-none')) {
                                    // WhatsApp uses SMS credentials, no validation needed
                                    break;
                                }
                                
                                // Otherwise validate WhatsApp Twilio fields
                                const whatsappFields = ['twilio_account_sid', 'twilio_auth_token', 'twilio_phone_number'];
                                whatsappFields.forEach(fieldId => {
                                    const field = document.getElementById(fieldId);
                                    if (field && !field.value.trim()) {
                                        field.classList.add('is-invalid');
                                        isValid = false;
                                    }
                                });
                                break;
                                
                            case 'messenger':
                                const messengerFields = ['page_id', 'page_name', 'messenger_access_token'];
                                messengerFields.forEach(fieldId => {
                                    const field = document.getElementById(fieldId);
                                    if (field && !field.value.trim()) {
                                        field.classList.add('is-invalid');
                                        isValid = false;
                                    }
                                });
                                break;
                                
                            case 'sms':
                                // Check if WhatsApp is selected first
                                const whatsappCheckboxForSms = document.getElementById('channel_whatsapp');
                                const smsWhatsappSharedInfo = document.getElementById('sms_whatsapp_shared_info');
                                
                                // If WhatsApp is selected first, no need to validate SMS fields
                                if (whatsappCheckboxForSms && whatsappCheckboxForSms.checked && 
                                    smsWhatsappSharedInfo && !smsWhatsappSharedInfo.classList.contains('d-none')) {
                                    // SMS uses WhatsApp credentials, no validation needed
                                    break;
                                }
                                
                                // Otherwise validate SMS Twilio fields
                                const smsFields = ['sms_twilio_account_sid', 'sms_twilio_auth_token', 'sms_twilio_phone_number'];
                                smsFields.forEach(fieldId => {
                                    const field = document.getElementById(fieldId);
                                    if (field && !field.value.trim()) {
                                        field.classList.add('is-invalid');
                                        isValid = false;
                                    }
                                });
                                break;
                                
                            case 'web':
                                // No additional fields needed for web
                                break;
                        }
                    }
                });
            }
        }
        
        return isValid;
    }

    function updateModelOptions() {
        if (!llmProviderSelect || !llmModelSelect) return;
        
        // Clear existing options
        llmModelSelect.innerHTML = '';
        
        // Add new options based on selected provider
        const provider = llmProviderSelect.value;
        
        if (provider === 'openai') {
            addModelOption('gpt-3.5-turbo', 'GPT-3.5 Turbo');
            addModelOption('gpt-4', 'GPT-4');
            addModelOption('gpt-4-turbo', 'GPT-4 Turbo');
        } else if (provider === 'anthropic') {
            addModelOption('claude-2', 'Claude 2');
            addModelOption('claude-instant', 'Claude Instant');
        } else if (provider === 'google') {
            addModelOption('gemini-pro', 'Gemini Pro');
            addModelOption('gemini-ultra', 'Gemini Ultra');
        } else if (provider === 'mistral') {
            addModelOption('mistral-small', 'Mistral Small');
            addModelOption('mistral-medium', 'Mistral Medium');
            addModelOption('mistral-large', 'Mistral Large');
        } else if (provider === 'llama') {
            addModelOption('llama-3-8b', 'Llama 3 8B');
            addModelOption('llama-3-70b', 'Llama 3 70B');
        } else if (provider === 'custom') {
            addModelOption('custom', 'Custom Model');
        }
    }

    function addModelOption(value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        llmModelSelect.appendChild(option);
    }

    function getInitials(name) {
        return name
            .split(' ')
            .map(word => word.charAt(0))
            .join('')
            .toUpperCase()
            .substring(0, 2);
    }

    function getRandomColor() {
        const colors = [
            '#4F46E5', // Indigo
            '#10B981', // Emerald
            '#6366F1', // Violet
            '#8B5CF6', // Purple
            '#EC4899', // Pink
            '#EF4444', // Red
            '#F59E0B', // Amber
            '#3B82F6'  // Blue
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
}); 