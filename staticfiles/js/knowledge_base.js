document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.getElementById('kb-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const kbCards = document.querySelectorAll('.kb-card');
            
            kbCards.forEach(card => {
                const kbName = card.querySelector('.kb-name').textContent.toLowerCase();
                const chatbotName = card.querySelector('.text-muted strong').textContent.toLowerCase();
                const isVisible = kbName.includes(searchTerm) || chatbotName.includes(searchTerm);
                
                card.closest('.row').style.display = isVisible ? 'flex' : 'none';
            });
        });
    }

    // Filter functionality
    const filterButtons = document.querySelectorAll('.filter-buttons button');
    if (filterButtons.length) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Update active button
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                // Get filter type from button text
                const filterType = this.textContent.trim().toLowerCase();
                const kbCards = document.querySelectorAll('.kb-card');

                if (filterType === 'all') {
                    kbCards.forEach(card => {
                        card.closest('.row').style.display = 'flex';
                    });
                } else if (filterType === 'recent') {
                    // Here you would implement sorting by date
                    // This is a placeholder implementation
                    const sortedCards = Array.from(kbCards);
                    sortedCards.sort((a, b) => {
                        const dateA = new Date(a.querySelector('.kb-info p:nth-child(2)').textContent);
                        const dateB = new Date(b.querySelector('.kb-info p:nth-child(2)').textContent);
                        return dateB - dateA;
                    });
                    
                    // Hide all and then show in new order
                    kbCards.forEach(card => card.closest('.row').style.display = 'none');
                    sortedCards.forEach(card => card.closest('.row').style.display = 'flex');
                }
            });
        });
    }

    // Modal form validation and submission
    const createKnowledgeBaseForm = document.getElementById('createKnowledgeBaseForm');
    if (createKnowledgeBaseForm) {
        const submitButton = document.querySelector('#createKnowledgeBaseModal .btn-primary');
        if (submitButton) {
            submitButton.addEventListener('click', function(e) {
                const chatbotSelect = document.getElementById('chatbot');
                if (!chatbotSelect.value) {
                    e.preventDefault();
                    alert('Please select a chatbot for your knowledge base');
                    return false;
                }
                createKnowledgeBaseForm.submit();
            });
        }
    }

    // "Show more sources" functionality
    const showMoreButtons = document.querySelectorAll('.btn-sm.btn-link');
    showMoreButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Find the parent card and all hidden sources
            const cardBody = this.closest('.kb-card-body');
            const allSources = cardBody.querySelectorAll('.data-source-item');
            const hiddenSources = Array.from(allSources).slice(5);
            
            // Toggle visibility of hidden sources
            hiddenSources.forEach(source => {
                source.style.display = source.style.display === 'none' ? 'flex' : 'none';
            });
            
            // Update button text
            if (this.textContent.includes('Show')) {
                this.textContent = 'Show less';
            } else {
                this.textContent = `Show ${hiddenSources.length} more sources`;
            }
        });
    });
}); 