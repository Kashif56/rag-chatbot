document.addEventListener('DOMContentLoaded', function() {
    // Model dropdown population based on provider selection
    const providerSelect = document.getElementById('llm_provider');
    const modelSelect = document.getElementById('llm_model');
    
    const modelOptions = {
        'openai': [
            { value: 'gpt-4', text: 'GPT-4 Turbo' },
            { value: 'gpt-4o', text: 'GPT-4o' },
            { value: 'gpt-3.5-turbo', text: 'GPT-3.5 Turbo' }
        ],
        'google': [
            { value: 'gemini-1.5-pro-latest', text: 'Gemini 1.5 Pro' },
            { value: 'gemini-1.5-flash', text: 'Gemini 1.5 Flash' }
        ],
        'deepseek': [
            { value: 'deepseek-chat', text: 'DeepSeek Chat' },
            { value: 'deepseek-coder', text: 'DeepSeek Coder' }
        ],
        'anthropic': [
            { value: 'claude-3-opus', text: 'Claude 3 Opus' },
            { value: 'claude-3-sonnet', text: 'Claude 3 Sonnet' },
            { value: 'claude-3-haiku', text: 'Claude 3 Haiku' }
        ],
        'mistral': [
            { value: 'mistral-large', text: 'Mistral Large' },
            { value: 'mistral-medium', text: 'Mistral Medium' }
        ]
    };
    
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
                if (option.value === modelSelect.dataset.currentModel) {
                    optElement.selected = true;
                }
                modelSelect.appendChild(optElement);
            });
        }
    }
    
    // Initial population
    if (providerSelect) {
        updateModelOptions();
        
        // Update when provider changes
        providerSelect.addEventListener('change', updateModelOptions);
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
    
    // AJAX form submission
    const form = document.getElementById('chatbotEditForm');
    const saveButton = document.querySelector('.btn-save');
    
    if (form && saveButton) {
        saveButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            
            // Show loading state
            saveButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
            saveButton.disabled = true;
            
            fetch(form.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Reset button state
                saveButton.innerHTML = '<i class="fas fa-save me-2"></i>Save Changes';
                saveButton.disabled = false;
                
                // Show success toast
                const successToast = new bootstrap.Toast(document.getElementById('successToast'));
                successToast.show();
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Reset button state
                saveButton.innerHTML = '<i class="fas fa-save me-2"></i>Save Changes';
                saveButton.disabled = false;
                
                // Show error toast
                const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
                errorToast.show();
            });
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
}); 