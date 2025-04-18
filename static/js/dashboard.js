/**
 * NexusAI Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    // Toggle sidebar function
    function toggleSidebar() {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        
        // Store preference in localStorage
        if (sidebar.classList.contains('collapsed')) {
            localStorage.setItem('sidebarState', 'collapsed');
        } else {
            localStorage.setItem('sidebarState', 'expanded');
        }
    }
    
    // Check for saved state on page load
    const savedSidebarState = localStorage.getItem('sidebarState');
    if (savedSidebarState === 'collapsed') {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
    }
    
    // Set up toggle functionality for desktop
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            if (window.innerWidth >= 992) {
                // Desktop behavior - collapse sidebar
                toggleSidebar();
            } else {
                // Mobile behavior - toggle visibility
                e.stopPropagation();
                if (sidebar.classList.contains('d-none')) {
                    sidebar.classList.remove('d-none');
                    sidebar.classList.add('show');
                } else {
                    sidebar.classList.add('d-none');
                    sidebar.classList.remove('show');
                }
            }
        });
    }
    
    // Handle screen size changes
    function checkScreenSize() {
        if (window.innerWidth < 992) {
            // Mobile view - initially hide sidebar
            if (!sidebar.classList.contains('show')) {
                sidebar.classList.add('d-none');
                mainContent.classList.add('expanded');
            }
            
            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', function(event) {
                const isClickInside = sidebar.contains(event.target) || 
                                    (sidebarToggle && sidebarToggle.contains(event.target));
                
                if (!isClickInside && sidebar.classList.contains('show')) {
                    sidebar.classList.remove('show');
                    sidebar.classList.add('d-none');
                }
            });
        } else {
            // Desktop view - show sidebar (but respect collapsed state)
            sidebar.classList.remove('d-none', 'show');
            
            // Apply saved state from localStorage
            if (savedSidebarState === 'collapsed') {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('expanded');
            } else {
                sidebar.classList.remove('collapsed');
                mainContent.classList.remove('expanded');
            }
        }
    }
    
    // Check screen size on load
    checkScreenSize();
    
    // Check on resize
    window.addEventListener('resize', checkScreenSize);
    
    // Active navigation link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || currentPath.startsWith(href)) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // Tooltips initialization (for channel icons)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            boundary: document.body
        });
    });
    
    // Filter buttons in chatbot listing
    const filterButtons = document.querySelectorAll('.filter-buttons .btn');
    if (filterButtons.length) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Get filter value
                const filterValue = this.textContent.trim();
                
                // Perform filtering (demo only - in real app would filter the cards)
                console.log(`Filtering chatbots by: ${filterValue}`);
                
                // For demo, we'll just show a "loading" state
                const chatbotCards = document.querySelectorAll('.chatbot-card');
                chatbotCards.forEach(card => {
                    card.style.opacity = '0.6';
                });
                
                // Simulate loading
                setTimeout(() => {
                    chatbotCards.forEach(card => {
                        card.style.opacity = '1';
                        
                        // If filtering by Active/Inactive, show/hide cards accordingly
                        if (filterValue === 'All') {
                            card.closest('.col-md-6').style.display = 'block';
                        } else if (filterValue === 'Active') {
                            const badge = card.querySelector('.badge');
                            if (badge && badge.textContent.trim() === 'Active') {
                                card.closest('.col-md-6').style.display = 'block';
                            } else {
                                card.closest('.col-md-6').style.display = 'none';
                            }
                        } else if (filterValue === 'Inactive') {
                            const badge = card.querySelector('.badge');
                            if (badge && badge.textContent.trim() === 'Inactive') {
                                card.closest('.col-md-6').style.display = 'block';
                            } else {
                                card.closest('.col-md-6').style.display = 'none';
                            }
                        }
                    });
                }, 300);
            });
        });
    }
    
    // Search functionality
    const searchInput = document.querySelector('.chatbot-filters input[type="text"]');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const chatbotCards = document.querySelectorAll('.chatbot-card');
            
            chatbotCards.forEach(card => {
                const chatbotName = card.querySelector('.chatbot-name')?.textContent.toLowerCase() || '';
                const chatbotDesc = card.querySelector('.chatbot-description')?.textContent.toLowerCase() || '';
                
                if (chatbotName.includes(searchValue) || chatbotDesc.includes(searchValue)) {
                    card.closest('.col-md-6').style.display = 'block';
                } else {
                    card.closest('.col-md-6').style.display = 'none';
                }
            });
        });
    }
    
    // Dropdown menus in cards (three dots menu)
    const dropdownMenus = document.querySelectorAll('.dropdown-menu');
    dropdownMenus.forEach(menu => {
        menu.addEventListener('click', function(e) {
            if (e.target.classList.contains('dropdown-item')) {
                const action = e.target.textContent.trim();
                const chatbotName = e.target.closest('.chatbot-card').querySelector('.chatbot-name').textContent;
                
                console.log(`Action "${action}" performed on chatbot: ${chatbotName}`);
                
                // For demo purposes, show an alert for delete action
                if (action.includes('Delete')) {
                    if (confirm(`Are you sure you want to delete "${chatbotName}"?`)) {
                        // Simulate deletion with fade out
                        const card = e.target.closest('.col-md-6');
                        card.style.transition = 'opacity 0.5s ease';
                        card.style.opacity = '0';
                        
                        setTimeout(() => {
                            card.style.display = 'none';
                        }, 500);
                    }
                }
            }
        });
    });
}); 