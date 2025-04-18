document.addEventListener('DOMContentLoaded', function() {
    // Navbar scroll effect
    const navbar = document.getElementById('mainNav');
    
    function checkScroll() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    }
    
    window.addEventListener('scroll', checkScroll);
    checkScroll(); // Check on initial load
    
    // Animate elements on scroll
    const animateElements = document.querySelectorAll('.feature-card, .timeline-item, .testimonial-card');
    
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.2
        });
        
        animateElements.forEach(el => {
            observer.observe(el);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        animateElements.forEach(el => {
            el.classList.add('animated');
        });
    }
    
    // Pricing toggle functionality
    const toggle = document.getElementById('billingToggle');
    
    if (toggle) {
        const monthlyPrices = ['0', '49', 'Custom'];
        const annualPrices = ['0', '39', 'Custom'];
        const amountElements = document.querySelectorAll('.amount');
        
        toggle.addEventListener('change', function() {
            const prices = this.checked ? annualPrices : monthlyPrices;
            const periods = this.checked ? '/year' : '/month';
            
            // Update displayed prices
            amountElements.forEach((el, index) => {
                if (index < prices.length) {
                    el.textContent = prices[index];
                }
            });
            
            // Update period text
            document.querySelectorAll('.period').forEach(el => {
                el.textContent = periods;
            });
        });
    }
    
    // Simulate chat typing effect in demo section
    const demoChat = document.querySelector('.chat-typing');
    
    if (demoChat) {
        setTimeout(() => {
            demoChat.style.display = 'none';
            
            const newMessage = document.createElement('div');
            newMessage.className = 'chat-message bot-message';
            newMessage.innerHTML = `
                <p>The Pro plan includes:</p>
                <ul>
                    <li>5 custom chatbots</li>
                    <li>10,000 messages per month</li>
                    <li>Advanced AI capabilities</li>
                    <li>Multi-channel support</li>
                    <li>Analytics dashboard</li>
                    <li>Custom branding</li>
                    <li>Basic integrations with other tools</li>
                </ul>
                <p>Would you like to sign up for a free trial of our Pro plan?</p>
            `;
            
            const chatBody = document.querySelector('.chat-window-body');
            chatBody.appendChild(newMessage);
            chatBody.scrollTop = chatBody.scrollHeight;
        }, 3000);
    }
}); 