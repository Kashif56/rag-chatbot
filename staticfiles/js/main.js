/**
 * RAG Chatbot Main JavaScript File
 * Handles all interactive elements and functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Chat functionality (if chat container exists)
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        initChat();
    }

    // Pricing toggle (if pricing toggle exists)
    const pricingToggle = document.querySelector('.pricing-toggle');
    if (pricingToggle) {
        initPricingToggle();
    }

    // Contact form validation (if contact form exists)
    const contactForm = document.querySelector('form');
    if (contactForm) {
        initContactForm(contactForm);
    }

    // Initialize AOS (Animate on Scroll)
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true,
        mirror: false
    });

    // Navbar scroll behavior
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Interactive typing effect for demo
    const typingElement = document.querySelector('.typing-effect');
    if (typingElement) {
        const phrases = [
            "Upload your PDF documents and ask questions...",
            "How does solar energy work?",
            "Summarize the key findings from the Q3 report.",
            "What are the side effects of medication X?",
            "Find regulations related to data privacy in the EU."
        ];

        let i = 0;
        let j = 0;
        let currentPhrase = [];
        let isDeleting = false;
        let isEnd = false;

        function loop() {
            isEnd = false;
            if (typingElement) {
                typingElement.innerHTML = currentPhrase.join('');

                if (i < phrases.length) {
                    // If not deleting and haven't reached end of phrase
                    if (!isDeleting && j <= phrases[i].length) {
                        currentPhrase.push(phrases[i][j]);
                        j++;
                    }

                    // If deleting
                    if (isDeleting && j <= phrases[i].length) {
                        currentPhrase.pop();
                        j--;
                    }

                    // If reached end of phrase
                    if (j == phrases[i].length) {
                        isEnd = true;
                        isDeleting = true;
                    }

                    // If deleted entire phrase
                    if (isDeleting && j === 0) {
                        currentPhrase = [];
                        isDeleting = false;
                        i++;
                        // Loop back to first phrase
                        if (i === phrases.length) {
                            i = 0;
                        }
                    }
                }

                // Speed settings
                const normalSpeed = 100;
                const deleteSpeed = 50;
                const pauseDelay = 1000;
                
                let time = isEnd ? pauseDelay : isDeleting ? deleteSpeed : normalSpeed;
                setTimeout(loop, time);
            }
        }

        loop();
    }

    // Demo chat functionality
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessagesContainer = document.querySelector('.chat-container');

    if (chatForm && chatInput && chatMessagesContainer) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (message !== '') {
                // Add user message
                addMessage(message, 'user');
                chatInput.value = '';
                
                // Simulate thinking
                setTimeout(() => {
                    // Add bot response - could be replaced with actual API call
                    simulateResponse(message);
                }, 1000);
            }
        });
    }

    function addMessage(message, sender) {
        if (!chatMessagesContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message');
        if (sender === 'user') {
            messageElement.classList.add('user');
        }
        
        const avatarSrc = sender === 'user' 
            ? '/static/images/user-avatar.png'  // Replace with actual path
            : '/static/images/assistant-avatar.png';  // Replace with actual path

        messageElement.innerHTML = `
            <div class="chat-avatar">
                <img src="${avatarSrc}" alt="${sender} avatar">
            </div>
            <div class="chat-bubble">
                ${message}
            </div>
        `;
        
        chatMessagesContainer.appendChild(messageElement);
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }

    function simulateResponse(userMessage) {
        const responses = {
            default: "I'm your RAG Assistant. I can help you find information from your documents. Upload a document to get started!",
            greeting: ["Hello!", "Hi there!", "Greetings! How can I help you today?"],
            question: "Based on the documents you've uploaded, I found the following information: [simulated document search result]",
            upload: "Great! I've processed your document. You can now ask questions about it.",
            help: "I can answer questions based on documents you upload. Try uploading a PDF and asking specific questions about its content."
        };
        
        let response = '';
        
        // Simple logic to determine response type - this would be much more sophisticated in a real implementation
        const lowerMessage = userMessage.toLowerCase();
        
        if (lowerMessage.includes('hello') || lowerMessage.includes('hi ') || lowerMessage === 'hi') {
            const randomIndex = Math.floor(Math.random() * responses.greeting.length);
            response = responses.greeting[randomIndex];
        } else if (lowerMessage.includes('help') || lowerMessage.includes('what can you do')) {
            response = responses.help;
        } else if (lowerMessage.includes('upload') || lowerMessage.includes('document') || lowerMessage.includes('pdf')) {
            response = responses.upload;
        } else if (lowerMessage.includes('?')) {
            response = responses.question;
        } else {
            response = responses.default;
        }
        
        addMessage(response, 'assistant');
    }

    // File upload preview
    const fileUpload = document.getElementById('file-upload');
    const filePreview = document.getElementById('file-preview');
    
    if (fileUpload && filePreview) {
        fileUpload.addEventListener('change', function() {
            filePreview.innerHTML = '';
            
            if (this.files && this.files.length > 0) {
                const fileList = document.createElement('div');
                fileList.classList.add('file-list');
                
                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];
                    const fileItem = document.createElement('div');
                    fileItem.classList.add('file-item');
                    
                    // Create appropriate icon based on file type
                    let iconClass = 'fa-file';
                    if (file.type.includes('pdf')) iconClass = 'fa-file-pdf';
                    else if (file.type.includes('word')) iconClass = 'fa-file-word';
                    else if (file.type.includes('excel') || file.type.includes('spreadsheet')) iconClass = 'fa-file-excel';
                    else if (file.type.includes('image')) iconClass = 'fa-file-image';
                    
                    // Format file size
                    const fileSize = formatFileSize(file.size);
                    
                    fileItem.innerHTML = `
                        <div class="file-icon"><i class="fas ${iconClass}"></i></div>
                        <div class="file-info">
                            <div class="file-name">${file.name}</div>
                            <div class="file-size">${fileSize}</div>
                        </div>
                        <div class="file-remove"><i class="fas fa-times"></i></div>
                    `;
                    
                    fileList.appendChild(fileItem);
                }
                
                filePreview.appendChild(fileList);
                
                // Add remove functionality
                document.querySelectorAll('.file-remove').forEach(button => {
                    button.addEventListener('click', function() {
                        this.closest('.file-item').remove();
                        // If no files left, reset file input
                        if (document.querySelectorAll('.file-item').length === 0) {
                            fileUpload.value = '';
                        }
                    });
                });
            }
        });
    }
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }

    // Pricing toggle
    const pricingToggleSwitch = document.getElementById('pricing-toggle');
    const monthlyPrices = document.querySelectorAll('.price-monthly');
    const yearlyPrices = document.querySelectorAll('.price-yearly');
    
    if (pricingToggleSwitch && monthlyPrices.length && yearlyPrices.length) {
        pricingToggleSwitch.addEventListener('change', function() {
            if (this.checked) {
                // Show yearly prices
                monthlyPrices.forEach(el => el.style.display = 'none');
                yearlyPrices.forEach(el => el.style.display = 'block');
            } else {
                // Show monthly prices
                monthlyPrices.forEach(el => el.style.display = 'block');
                yearlyPrices.forEach(el => el.style.display = 'none');
            }
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    if (forms.length > 0) {
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            }, false);
        });
    }
    
    // Tooltip initialization
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Counter animation for statistics
    const counters = document.querySelectorAll('.counter-value');
    
    if (counters.length > 0) {
        const animateCounter = (counter, start = 0, end, duration = 2000) => {
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                const value = Math.floor(progress * (end - start) + start);
                counter.innerHTML = value.toLocaleString();
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        };
        
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const end = parseInt(counter.getAttribute('data-target'));
                    animateCounter(counter, 0, end);
                    observer.unobserve(counter);
                }
            });
        }, { threshold: 0.2 });
        
        counters.forEach(counter => {
            observer.observe(counter);
        });
    }
});

/**
 * Initialize chat functionality
 */
function initChat() {
    const chatMessages = document.querySelector('.chat-messages');
    const chatForm = document.querySelector('.chat-form');
    const chatInput = document.querySelector('.chat-input input');
    
    if (!chatForm || !chatInput || !chatMessages) return;
    
    // Auto-scroll to bottom of messages
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add a new message to the chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
        messageDiv.textContent = message;
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input
        chatInput.value = '';
        
        // In a real app, this is where you would send the message to the backend
        // For now, we'll just simulate a response after a delay
        const loadingIndicator = document.createElement('div');
        loadingIndicator.classList.add('message', 'bot-message', 'loading');
        loadingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        chatMessages.appendChild(loadingIndicator);
        scrollToBottom();
        
        setTimeout(() => {
            chatMessages.removeChild(loadingIndicator);
            addMessage("This is a simulated response. In the real application, this would be handled by the RAG Chatbot backend.");
        }, 1500);
    });
    
    // Initial scroll to bottom
    scrollToBottom();
}

/**
 * Initialize pricing toggle functionality
 */
function initPricingToggle() {
    const monthlyBtn = document.getElementById('monthly-pricing');
    const annualBtn = document.getElementById('annual-pricing');
    const monthlyPrices = document.querySelectorAll('.monthly-price');
    const annualPrices = document.querySelectorAll('.annual-price');
    
    if (!monthlyBtn || !annualBtn) return;
    
    monthlyBtn.addEventListener('click', function() {
        this.classList.add('active');
        annualBtn.classList.remove('active');
        monthlyPrices.forEach(el => el.classList.remove('d-none'));
        annualPrices.forEach(el => el.classList.add('d-none'));
    });
    
    annualBtn.addEventListener('click', function() {
        this.classList.add('active');
        monthlyBtn.classList.remove('active');
        annualPrices.forEach(el => el.classList.remove('d-none'));
        monthlyPrices.forEach(el => el.classList.add('d-none'));
    });
}

/**
 * Initialize contact form validation
 */
function initContactForm(form) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Simple validation
        let valid = true;
        form.querySelectorAll('[required]').forEach(input => {
            if (!input.value.trim()) {
                valid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });
        
        // Email validation
        const emailInput = form.querySelector('input[type="email"]');
        if (emailInput && emailInput.value.trim()) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailInput.value.trim())) {
                valid = false;
                emailInput.classList.add('is-invalid');
            }
        }
        
        if (valid) {
            // In a real app, this is where you would submit the form data
            // For now, we'll just show a success message
            const submitButton = form.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
            
            setTimeout(() => {
                // Create success alert
                const successAlert = document.createElement('div');
                successAlert.classList.add('alert', 'alert-success', 'mt-3');
                successAlert.textContent = 'Your message has been sent successfully!';
                
                // Insert alert after form
                form.parentNode.insertBefore(successAlert, form.nextSibling);
                
                // Reset form
                form.reset();
                submitButton.disabled = false;
                submitButton.textContent = originalText;
                
                // Remove alert after 5 seconds
                setTimeout(() => {
                    successAlert.remove();
                }, 5000);
            }, 1500);
        }
    });
    
    // Real-time validation feedback
    form.querySelectorAll('input, textarea, select').forEach(input => {
        input.addEventListener('input', function() {
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
            
            // Email validation
            if (this.type === 'email' && this.value.trim()) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(this.value.trim())) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                }
            }
        });
    });
} 