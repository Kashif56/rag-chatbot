document.addEventListener('DOMContentLoaded', function() {
    // Model dropdown population based on provider selection
    const providerSelect = document.getElementById('llm_provider');
    const modelSelect = document.getElementById('llm_model');
    
    const modelOptions = {
        'openai': [
            { value: 'gpt-4o-mini', text: 'GPT-4o Mini' },
            { value: 'gpt-4o', text: 'GPT-4o' },
            { value: 'gpt-4', text: 'GPT-4' },
            { value: 'gpt-3.5-turbo', text: 'GPT-3.5 Turbo' }
        ],
        'google': [
            { value: 'gemini-1.5-pro-latest', text: 'Gemini 1.5 Pro' }
        ],
        'deepseek': [
            { value: 'deepseek-chat', text: 'DeepSeek Chat' }
        ]
    };
    
    // Function to update model options based on selected provider
    function updateModelOptions() {
        const provider = providerSelect.value;
        
        // Clear current options
        modelSelect.innerHTML = '';
        
        // Add new options based on provider
        if (modelOptions[provider]) {
            modelOptions[provider].forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option.value;
                optElement.textContent = option.text;
                
                // Set as selected if it matches the current model
                if (option.value === window.chatbotData.llm_model) {
                    optElement.selected = true;
                }
                
                modelSelect.appendChild(optElement);
            });
        }
    }
    
    // Initialize form with data from server
    populateFormWithData();
    
    // Add event listener for provider changes
    if (providerSelect) {
        providerSelect.addEventListener('change', updateModelOptions);
    }
    
    // Populate form with data from backend
    function populateFormWithData() {
        // Basic info
        const chatbot = window.chatbotData || {};
        
        // Populate chatbot name
        const nameDisplay = document.getElementById('chatbotNameDisplay');
        const nameInput = document.getElementById('chatbot_name');
        if (nameDisplay && nameInput && chatbot.name) {
            nameDisplay.innerHTML = `<i class="fas fa-robot me-2"></i>${chatbot.name}`;
            nameInput.value = chatbot.name;
        }
        
        // Populate description
        const descriptionField = document.getElementById('chatbot_description');
        if (descriptionField && chatbot.description) {
            descriptionField.value = chatbot.description;
        }
        
        // Populate prompt
        const promptField = document.getElementById('chatbot_prompt');
        if (promptField && chatbot.prompt) {
            promptField.value = chatbot.prompt;
        }
        
        // Populate model settings
        if (providerSelect && chatbot.llm_provider) {
            // Set provider first
            providerSelect.value = chatbot.llm_provider;
            
            // Then update model options and select the correct model
            updateModelOptions();
        }
        
        // Populate is_active and is_public checkboxes
        const isActiveCheckbox = document.getElementById('is_active');
        const isPublicCheckbox = document.getElementById('is_public');
        
        if (isActiveCheckbox && chatbot.hasOwnProperty('is_active')) {
            isActiveCheckbox.checked = chatbot.is_active;
        }
        
        if (isPublicCheckbox && chatbot.hasOwnProperty('is_public')) {
            isPublicCheckbox.checked = chatbot.is_public;
        }
        
        // Populate channels list
        populateChannelsList();
    }
    
    // Populate channels list
    function populateChannelsList() {
        // Skip if we're using Django template rendering for channels list
        if (document.querySelector('.channels-list').children.length > 0) {
            return;
        }
        
        const channelsContainer = document.querySelector('.channels-list');
        if (!channelsContainer) return;
        
        const channelsData = window.channelsData || [];
        if (channelsData.length === 0) return;
        
        // Clear existing channels
        channelsContainer.innerHTML = '';
        
        // Add channel rows
        channelsData.forEach(channel => {
            let iconClass;
            switch(channel.channel_type.toLowerCase()) {
                case 'web chat': 
                case 'web': iconClass = 'fa-globe'; break;
                case 'whatsapp': iconClass = 'fa-whatsapp'; break;
                case 'messenger': iconClass = 'fa-facebook-messenger'; break;
                case 'sms': iconClass = 'fa-sms'; break;
                case 'email': iconClass = 'fa-envelope'; break;
                default: iconClass = 'fa-comment'; break;
            }
            
            const channelRow = document.createElement('div');
            channelRow.className = 'channel-row d-flex justify-content-between align-items-center mb-2 p-2 rounded';
            channelRow.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="channel-icon ${channel.channel_type.toLowerCase().replace(/\s/g, '')} me-2">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <span>${channel.channel_type}</span>
                </div>
                <div>
                    <span class="badge bg-success me-2">Active</span>
                    <button type="button" class="btn btn-sm btn-outline-primary manage-channel-btn" 
                            data-channel-type="${channel.channel_type.toLowerCase().replace(/\s/g, '')}" 
                            data-channel-id="${channel.channel_id || ''}"
                            data-channel-name="${channel.channel_type}">
                        Manage
                    </button>
                </div>
            `;
            
            channelsContainer.appendChild(channelRow);
        });
        
        // Add event listeners for manage buttons
        document.querySelectorAll('.manage-channel-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const channelType = this.getAttribute('data-channel-type');
                const channelName = this.getAttribute('data-channel-name');
                const channelId = this.getAttribute('data-channel-id');
                
                openChannelManagementModal(channelType, channelName, channelId);
            });
        });
    }
    
    function getChannelName(channelType) {
        const channelNames = {
            'web': 'Web Chat',
            'whatsapp': 'WhatsApp',
            'messenger': 'Messenger',
            'sms': 'SMS',
            'email': 'Email'
        };
        
        return channelNames[channelType] || channelType;
    }
    
    function openChannelManagementModal(channelType, channelName, channelId) {
        // Update modal title
        document.getElementById('channelTypeText').textContent = channelName;
        
        // Hide all channel-specific settings
        document.querySelectorAll('.channel-specific-settings').forEach(el => {
            el.classList.add('d-none');
        });
        
        // Show only the relevant settings
        const settingsEl = document.getElementById(channelType + 'Settings');
        if (settingsEl) {
            settingsEl.classList.remove('d-none');
        }
        
        // Populate channel form with data
        populateChannelForm(channelType, channelId);
        
        // Show modal
        const channelManagementModal = new bootstrap.Modal(document.getElementById('channelManagementModal'));
        channelManagementModal.show();
    }
    
    function populateChannelForm(channelType, channelId) {
        const channelsData = window.channelsData || [];
        const channel = channelsData.find(c => c.channel_id === channelId);
        
        if (!channel) return;
        
        // Populate specific channel data based on type
        switch(channelType) {
            case 'email':
                if (channel.email_config) {
                    document.getElementById('emailAddress').value = channel.email_config.email_address || '';
                    document.getElementById('emailProvider').value = channel.email_config.provider || '';
                    document.getElementById('emailAccessToken').value = channel.email_config.access_token || '';
                    document.getElementById('emailRefreshToken').value = channel.email_config.refresh_token || '';
                    document.getElementById('smtpServer').value = channel.email_config.smtp_server || '';
                    document.getElementById('smtpPort').value = channel.email_config.smtp_port || '';
                    document.getElementById('imapServer').value = channel.email_config.imap_server || '';
                    document.getElementById('imapPort').value = channel.email_config.imap_port || '';
                }
                break;
                
            case 'whatsapp':
                if (channel.whatsapp_config) {
                    document.getElementById('twilioAccountSid').value = channel.whatsapp_config.twilio_account_sid || '';
                    document.getElementById('twilioAuthToken').value = channel.whatsapp_config.twilio_auth_token || '';
                    document.getElementById('twilioPhoneNumber').value = channel.whatsapp_config.twilio_phone_number || '';
                }
                break;
                
            case 'messenger':
                if (channel.messenger_config) {
                    document.getElementById('pageId').value = channel.messenger_config.page_id || '';
                    document.getElementById('pageName').value = channel.messenger_config.page_name || '';
                    document.getElementById('accessToken').value = channel.messenger_config.access_token || '';
                }
                break;
        }
    }
    
    // Temperature slider and input sync
    const temperatureRange = document.getElementById('temperature_range');
    const temperatureInput = document.getElementById('temperature');
    
    if (temperatureRange && temperatureInput) {
        temperatureRange.addEventListener('input', function() {
            temperatureInput.value = this.value;
        });
        
        temperatureInput.addEventListener('input', function() {
            temperatureRange.value = this.value;
        });
    }
    
    // Collapsible sections handling
    const collapsibleSections = document.querySelectorAll('.settings-header[data-bs-toggle="collapse"]');
    
    collapsibleSections.forEach(section => {
        // Get the target element id
        const targetId = section.getAttribute('data-bs-target').substring(1);
        const targetElement = document.getElementById(targetId);
        
        // Initialize Bootstrap collapse
        const collapseElement = new bootstrap.Collapse(targetElement, {
            toggle: false
        });
        
        // Update icon based on initial state
        updateToggleIcon(section);
        
        // Add event listener for changes
        section.addEventListener('click', function() {
            // Toggle will happen automatically via bootstrap data attributes
            // We just need to update the icon after a small delay to allow the collapse to start
            setTimeout(() => {
                updateToggleIcon(this);
            }, 50);
        });
    });
    
    function updateToggleIcon(section) {
        const isExpanded = section.getAttribute('aria-expanded') === 'true';
        const icon = section.querySelector('.toggle-icon');
        
        if (isExpanded) {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
        } else {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
        }
    }
    
    // Full screen prompt editor
    const expandPromptBtn = document.getElementById('expandPrompt');
    const promptEditorModal = new bootstrap.Modal(document.getElementById('promptEditorModal'));
    const promptTextarea = document.getElementById('chatbot_prompt');
    const fullScreenPrompt = document.getElementById('fullScreenPrompt');
    const applyPromptChangesBtn = document.getElementById('applyPromptChanges');
    
    if (expandPromptBtn && promptTextarea && fullScreenPrompt && applyPromptChangesBtn) {
        // Prevent default resize behavior
        promptTextarea.addEventListener('input', function() {
            this.style.height = '200px';
        });
        
        expandPromptBtn.addEventListener('click', function() {
            fullScreenPrompt.value = promptTextarea.value;
            promptEditorModal.show();
        });
        
        applyPromptChangesBtn.addEventListener('click', function() {
            promptTextarea.value = fullScreenPrompt.value;
            promptEditorModal.hide();
        });
    }
    
    // Handle delete button
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            // Show loading state
            confirmDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Deleting...';
            confirmDeleteBtn.disabled = true;
            
            const chatbotId = confirmDeleteBtn.dataset.chatbotId;
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(`/dashboard/chatbots/${chatbotId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/dashboard/chatbots/';
                } else {
                    // Reset button state
                    confirmDeleteBtn.innerHTML = '<i class="fas fa-trash-alt me-1"></i>Delete Permanently';
                    confirmDeleteBtn.disabled = false;
                    
                    // Show error message
                    const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
                    errorToast.show();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Reset button state
                confirmDeleteBtn.innerHTML = '<i class="fas fa-trash-alt me-1"></i>Delete Permanently';
                confirmDeleteBtn.disabled = false;
                
                // Show error toast
                const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
                errorToast.show();
            });
        });
    }
    
    // Chat functionality
    const messageInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');
    
    if (messageInput && sendButton && chatMessages) {
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (message === '') return;
            
            // Add user message to chat
            appendMessage('user', message);
            messageInput.value = '';
            
            // Simulate bot response after a short delay
            sendButton.disabled = true;
            setTimeout(function() {
                const responses = [
                    "I'm processing that information now.",
                    "That's an interesting point. Let me think about that.",
                    "Thanks for sharing that with me. Is there anything else you'd like to discuss?",
                    "I understand what you're asking. Here's what I can tell you...",
                    "Based on my knowledge, I would suggest considering the following..."
                ];
                const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                appendMessage('bot', randomResponse);
                sendButton.disabled = false;
            }, 1000);
        }
        
        function appendMessage(sender, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${sender}-message mb-3`;
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            
            const messagePara = document.createElement('p');
            messagePara.className = 'mb-0';
            messagePara.textContent = content;
            
            messageContent.appendChild(messagePara);
            messageDiv.appendChild(messageContent);
            chatMessages.appendChild(messageDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // Add channel functionality
    const addChannelBtn = document.getElementById('addChannelBtn');
    const addNewChannelBtn = document.getElementById('addNewChannelBtn');
    const addChannelModal = document.getElementById('addChannelModal') ? new bootstrap.Modal(document.getElementById('addChannelModal')) : null;
    
    if (addChannelBtn && addNewChannelBtn && addChannelModal) {
        // When Add Channel button is clicked
        addChannelBtn.addEventListener('click', function() {
            // Show available channels
            populateAvailableChannels();
            
            // Show modal
            addChannelModal.show();
        });
        
        // When back button is clicked
        document.querySelector('.back-to-selection')?.addEventListener('click', function() {
            document.querySelector('.channel-selection').classList.remove('d-none');
            document.getElementById('channelConfigSection').classList.add('d-none');
            document.getElementById('addNewChannelBtn').classList.add('d-none');
        });
        
        // When Add New Channel button is clicked
        addNewChannelBtn.addEventListener('click', function() {
            const form = document.getElementById('newChannelForm');
            const formData = new FormData(form);
            
            // Convert FormData to JSON
            const channelData = {};
            formData.forEach((value, key) => {
                channelData[key] = value;
            });
            
            // Show loading state
            addNewChannelBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
            addNewChannelBtn.disabled = true;
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Get chatbot ID from the data
            const chatbotId = window.chatbotData.chatbot_id;
            
            // Send API request
            fetch(`/chat/add-channel/${chatbotId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(channelData)
            })
            .then(response => response.json())
            .then(data => {
                // Reset button state
                addNewChannelBtn.innerHTML = 'Add Channel';
                addNewChannelBtn.disabled = false;
                
                if (data.success) {
                    // Show success toast
                    const successToast = new bootstrap.Toast(document.getElementById('successToast'));
                    successToast.show();
                    
                    // Close modal
                    addChannelModal.hide();
                    
                    // Refresh the page to show the new channel
                    window.location.reload();
                } else {
                    // Show error message
                    alert(data.error || 'An error occurred. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Reset button state
                addNewChannelBtn.innerHTML = 'Add Channel';
                addNewChannelBtn.disabled = false;
                
                // Show error message
                alert('An error occurred. Please try again.');
            });
        });
    }
    
    function populateAvailableChannels() {
        const availableChannelsContainer = document.getElementById('availableChannelsContainer');
        if (!availableChannelsContainer) return;
        
        // Clear existing content
        availableChannelsContainer.innerHTML = '';
        
        // Get current channel types
        const currentChannels = Array.from(document.querySelectorAll('.channel-row')).map(row => {
            const button = row.querySelector('.manage-channel-btn');
            return button ? button.getAttribute('data-channel-type') : '';
        });
        
        // All available channels
        const allChannels = [
            { type: 'web', name: 'Web Chat', icon: 'fa-globe' },
            { type: 'whatsapp', name: 'WhatsApp', icon: 'fa-whatsapp' },
            { type: 'messenger', name: 'Messenger', icon: 'fa-facebook-messenger' },
            { type: 'sms', name: 'SMS', icon: 'fa-sms' },
            { type: 'email', name: 'Email', icon: 'fa-envelope' }
        ];
        
        // Filter out already added channels
        const availableChannels = allChannels.filter(channel => 
            !currentChannels.includes(channel.type.toLowerCase())
        );
        
        // Add available channels to the modal
        availableChannels.forEach(channel => {
            const channelCard = document.createElement('div');
            channelCard.className = 'col-md-6 mb-3';
            channelCard.innerHTML = `
                <div class="card h-100 channel-option" data-channel-type="${channel.type}">
                    <div class="card-body text-center py-4">
                        <div class="channel-icon ${channel.type} mb-3 mx-auto">
                            <i class="fas ${channel.icon} fa-2x"></i>
                        </div>
                        <h6 class="card-title">${channel.name}</h6>
                    </div>
                </div>
            `;
            availableChannelsContainer.appendChild(channelCard);
            
            // Add click handler
            channelCard.querySelector('.card-body').addEventListener('click', function() {
                const selectedType = this.closest('.channel-option').getAttribute('data-channel-type');
                showChannelConfiguration(selectedType);
            });
        });
    }
    
    function showChannelConfiguration(channelType) {
        // Find channel details
        const allChannels = [
            { type: 'web', name: 'Web Chat', icon: 'fa-globe' },
            { type: 'whatsapp', name: 'WhatsApp', icon: 'fa-whatsapp' },
            { type: 'messenger', name: 'Messenger', icon: 'fa-facebook-messenger' },
            { type: 'sms', name: 'SMS', icon: 'fa-sms' },
            { type: 'email', name: 'Email', icon: 'fa-envelope' }
        ];
        
        const channelInfo = allChannels.find(c => c.type === channelType);
        
        // Update selected channel name
        document.getElementById('selectedChannelName').textContent = channelInfo.name;
        
        // Hide channel selection, show configuration
        document.querySelector('.channel-selection').classList.add('d-none');
        document.getElementById('channelConfigSection').classList.remove('d-none');
        document.getElementById('addNewChannelBtn').classList.remove('d-none');
        
        // Generate form based on channel type
        const formContainer = document.getElementById('newChannelForm');
        formContainer.innerHTML = '';
        
        // Common fields for all channels
        const commonFields = `
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <label class="form-label fw-semibold">Channel Status</label>
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" id="newChannelActive" name="is_active" checked>
                    </div>
                </div>
                <div class="form-text">Enable or disable this channel</div>
            </div>
            
            <input type="hidden" name="channel_type" value="${channelType}">
        `;
        
        formContainer.innerHTML += commonFields;
        
        // Channel-specific fields
        let specificFields = '';
        
        switch(channelType) {
            case 'email':
                specificFields = `
                    <div class="mb-3">
                        <label for="newEmailAddress" class="form-label">Email Address</label>
                        <input type="email" class="form-control" id="newEmailAddress" name="email_address" placeholder="support@example.com" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="newEmailProvider" class="form-label">Provider</label>
                        <select class="form-select" id="newEmailProvider" name="provider" required>
                            <option value="gmail">Gmail</option>
                            <option value="outlook">Outlook</option>
                            <option value="imap">IMAP</option>
                            <option value="smtp">SMTP Custom</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="newEmailAccessToken" class="form-label">Access Token</label>
                        <div class="input-group">
                            <input type="password" class="form-control" id="newEmailAccessToken" name="access_token" required>
                            <button class="btn btn-outline-secondary toggle-visibility" type="button">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div id="customServerSettings" class="d-none">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="newSmtpServer" class="form-label">SMTP Server</label>
                                    <input type="text" class="form-control" id="newSmtpServer" name="smtp_server" placeholder="smtp.gmail.com">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="newSmtpPort" class="form-label">SMTP Port</label>
                                    <input type="number" class="form-control" id="newSmtpPort" name="smtp_port" placeholder="587">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="newImapServer" class="form-label">IMAP Server</label>
                                    <input type="text" class="form-control" id="newImapServer" name="imap_server" placeholder="imap.gmail.com">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="newImapPort" class="form-label">IMAP Port</label>
                                    <input type="number" class="form-control" id="newImapPort" name="imap_port" placeholder="993">
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;
                
            case 'whatsapp':
                specificFields = `
                    <div class="mb-3">
                        <label for="newTwilioAccountSid" class="form-label">Twilio Account SID</label>
                        <input type="text" class="form-control" id="newTwilioAccountSid" name="twilio_account_sid" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="newTwilioAuthToken" class="form-label">Twilio Auth Token</label>
                        <div class="input-group">
                            <input type="password" class="form-control" id="newTwilioAuthToken" name="twilio_auth_token" required>
                            <button class="btn btn-outline-secondary toggle-visibility" type="button">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="newTwilioPhoneNumber" class="form-label">Twilio Phone Number</label>
                        <input type="text" class="form-control" id="newTwilioPhoneNumber" name="twilio_phone_number" placeholder="+1234567890" required>
                        <div class="form-text">Include country code (e.g., +1 for US)</div>
                    </div>
                `;
                break;
                
            case 'messenger':
                specificFields = `
                    <div class="mb-3">
                        <label for="newPageId" class="form-label">Facebook Page ID</label>
                        <input type="text" class="form-control" id="newPageId" name="page_id" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="newPageName" class="form-label">Page Name</label>
                        <input type="text" class="form-control" id="newPageName" name="page_name" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="newAccessToken" class="form-label">Access Token</label>
                        <div class="input-group">
                            <input type="password" class="form-control" id="newAccessToken" name="access_token" required>
                            <button class="btn btn-outline-secondary toggle-visibility" type="button">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                `;
                break;
                
            case 'sms':
                specificFields = `
                    <div class="mb-3">
                        <label for="smsProvider" class="form-label">SMS Provider</label>
                        <select class="form-select" id="smsProvider" name="provider" required>
                            <option value="twilio">Twilio</option>
                            <option value="messagebird">MessageBird</option>
                            <option value="nexmo">Nexmo/Vonage</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="smsApiKey" class="form-label">API Key</label>
                        <div class="input-group">
                            <input type="password" class="form-control" id="smsApiKey" name="api_key" required>
                            <button class="btn btn-outline-secondary toggle-visibility" type="button">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="smsPhoneNumber" class="form-label">Phone Number</label>
                        <input type="text" class="form-control" id="smsPhoneNumber" name="phone_number" placeholder="+1234567890" required>
                    </div>
                `;
                break;
            
            case 'web':
                specificFields = `
                    <div class="mb-3">
                        <label for="webPrimaryColor" class="form-label">Primary Color</label>
                        <input type="color" class="form-control form-control-color" id="webPrimaryColor" name="primary_color" value="#0d6efd">
                    </div>
                    
                    <div class="mb-3">
                        <label for="webPosition" class="form-label">Widget Position</label>
                        <select class="form-select" id="webPosition" name="widget_position">
                            <option value="bottom-right">Bottom Right</option>
                            <option value="bottom-left">Bottom Left</option>
                            <option value="top-right">Top Right</option>
                            <option value="top-left">Top Left</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="webWelcomeMessage" class="form-label">Welcome Message</label>
                        <textarea class="form-control" id="webWelcomeMessage" name="welcome_message" rows="2">How can I help you today?</textarea>
                    </div>
                `;
                break;
        }
        
        formContainer.innerHTML += specificFields;
        
        // Add event listeners for toggle visibility buttons
        document.querySelectorAll('.toggle-visibility').forEach(btn => {
            btn.addEventListener('click', function() {
                const input = this.previousElementSibling;
                const icon = this.querySelector('i');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
        });
        
        // Show/hide custom server settings for email
        if (channelType === 'email') {
            document.getElementById('newEmailProvider').addEventListener('change', function() {
                const serverSettings = document.getElementById('customServerSettings');
                if (this.value === 'imap' || this.value === 'smtp') {
                    serverSettings.classList.remove('d-none');
                } else {
                    serverSettings.classList.add('d-none');
                }
            });
        }
    }
}); 