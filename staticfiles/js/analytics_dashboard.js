/**
 * Analytics Dashboard JavaScript
 * Handles fetching data from API endpoints and updating the dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts
    initMessageVolumeChart();
    initUserEngagementChart();
    initChannelDistributionChart();
    
    // Load initial data
    loadDashboardData('all');
    
    // Set up time period selector
    setupTimePeriodSelector();
    
    // Set up refresh buttons
    setupRefreshButtons();
});

/**
 * Set up time period selector
 */
function setupTimePeriodSelector() {
    const timePeriodButtons = document.querySelectorAll('.time-period-selector button');
    
    timePeriodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            timePeriodButtons.forEach(btn => {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline-primary');
            });
            
            // Add active class to clicked button
            this.classList.remove('btn-outline-primary');
            this.classList.add('btn-primary');
            
            // Get selected time period
            const period = this.textContent.trim().toLowerCase();
            
            // Load data for selected time period
            loadDashboardData(period);
        });
    });
}

/**
 * Load dashboard data for the selected time period
 */
function loadDashboardData(period) {
    // Load KPI data
    loadTotalMessages(period);
    loadUniqueUsers(period);
    loadActiveChatbots(period);
    loadAvgResponseTime(period);
    
    // Load chart data
    loadMessageVolumeData(period);
    loadUserEngagementData(period);
    loadChannelDistributionData(period);
    
    // Load other components
    loadChatbotPerformanceData(period);
    loadRecentActivityData();
}

/**
 * Load total messages KPI
 */
function loadTotalMessages(period) {
    fetch(`/analytics/api/total-messages/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            const totalMessagesElement = document.querySelector('.stat-card.primary .stat-value');
            totalMessagesElement.textContent = formatNumber(data.total_messages);
        })
        .catch(error => console.error('Error loading total messages:', error));
}

/**
 * Load unique users KPI
 */
function loadUniqueUsers(period) {
    fetch(`/analytics/api/unique-users/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            const uniqueUsersElement = document.querySelector('.stat-card.success .stat-value');
            uniqueUsersElement.textContent = formatNumber(data.unique_users);
        })
        .catch(error => console.error('Error loading unique users:', error));
}

/**
 * Load active chatbots KPI
 */
function loadActiveChatbots(period) {
    fetch(`/analytics/api/active-chatbots/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            const activeChatbotsElement = document.querySelector('.stat-card.warning .stat-value');
            activeChatbotsElement.textContent = data.active_chatbots;
        })
        .catch(error => console.error('Error loading active chatbots:', error));
}

/**
 * Load average response time KPI
 */
function loadAvgResponseTime(period) {
    fetch(`/analytics/api/avg-response-time/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            const avgResponseTimeElement = document.querySelector('.stat-card.info .stat-value');
            avgResponseTimeElement.textContent = `${data.avg_response_time}s`;
        })
        .catch(error => console.error('Error loading average response time:', error));
}

/**
 * Initialize Message Volume Chart
 */
function initMessageVolumeChart() {
    const messageVolumeCtx = document.getElementById('messageVolumeChart').getContext('2d');
    window.messageVolumeChart = new Chart(messageVolumeCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Messages',
                data: [],
                backgroundColor: 'rgba(110, 142, 251, 0.1)',
                borderColor: 'rgba(110, 142, 251, 1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    padding: 10,
                    cornerRadius: 4,
                    caretSize: 6
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Load message volume data for the chart
 */
function loadMessageVolumeData(period) {
    fetch(`/analytics/api/message-volume/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            window.messageVolumeChart.data.labels = data.labels;
            window.messageVolumeChart.data.datasets[0].data = data.data;
            window.messageVolumeChart.update();
        })
        .catch(error => console.error('Error loading message volume data:', error));
}

/**
 * Initialize User Engagement Chart
 */
function initUserEngagementChart() {
    const userEngagementCtx = document.getElementById('userEngagementChart').getContext('2d');
    window.userEngagementChart = new Chart(userEngagementCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Active Users',
                    data: [],
                    backgroundColor: 'rgba(45, 204, 167, 0.7)',
                    borderColor: 'rgba(45, 204, 167, 1)',
                    borderWidth: 1
                },
                {
                    label: 'New Users',
                    data: [],
                    backgroundColor: 'rgba(110, 142, 251, 0.7)',
                    borderColor: 'rgba(110, 142, 251, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Load user engagement data for the chart
 */
function loadUserEngagementData(period) {
    fetch(`/analytics/api/user-engagement/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            window.userEngagementChart.data.labels = data.labels;
            window.userEngagementChart.data.datasets[0].data = data.active_users;
            window.userEngagementChart.data.datasets[1].data = data.new_users;
            window.userEngagementChart.update();
        })
        .catch(error => console.error('Error loading user engagement data:', error));
}

/**
 * Initialize Channel Distribution Chart
 */
function initChannelDistributionChart() {
    const channelDistributionCtx = document.getElementById('channelDistributionChart').getContext('2d');
    window.channelDistributionChart = new Chart(channelDistributionCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    'rgba(110, 142, 251, 0.8)',
                    'rgba(45, 204, 167, 0.8)',
                    'rgba(23, 162, 184, 0.8)',
                    'rgba(255, 193, 7, 0.8)'
                ],
                borderColor: [
                    'rgba(110, 142, 251, 1)',
                    'rgba(45, 204, 167, 1)',
                    'rgba(23, 162, 184, 1)',
                    'rgba(255, 193, 7, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 15
                    }
                }
            },
            cutout: '70%'
        }
    });
}

/**
 * Load channel distribution data for the chart and table
 */
function loadChannelDistributionData(period) {
    fetch(`/analytics/api/channel-distribution/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            // Update chart
            window.channelDistributionChart.data.labels = data.channels;
            window.channelDistributionChart.data.datasets[0].data = data.message_counts;
            window.channelDistributionChart.update();
            
            // Update table
            const tableBody = document.querySelector('.table-responsive table tbody');
            tableBody.innerHTML = '';
            
            const channelIcons = {
                'Web': '<i class="fas fa-globe me-2 text-primary"></i>',
                'WhatsApp': '<i class="fab fa-whatsapp me-2 text-success"></i>',
                'Messenger': '<i class="fab fa-facebook-messenger me-2 text-info"></i>',
                'Email': '<i class="fas fa-envelope me-2 text-warning"></i>'
            };
            
            data.channel_breakdown.forEach(channel => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${channelIcons[channel.channel]}${channel.channel}</td>
                    <td>${formatNumber(channel.messages)}</td>
                    <td>${formatNumber(channel.users)}</td>
                    <td>${channel.avg_response}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading channel distribution data:', error));
}

/**
 * Load chatbot performance data
 */
function loadChatbotPerformanceData(period) {
    fetch(`/analytics/api/chatbot-performance/?period=${period}`)
        .then(response => response.json())
        .then(data => {
            const chatbotList = document.querySelector('.chatbot-list');
            chatbotList.innerHTML = '';
            
            data.chatbots.forEach((chatbot, index) => {
                const chatbotItem = document.createElement('div');
                chatbotItem.className = `chatbot-item ${index === 0 ? 'active' : ''}`;
                chatbotItem.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <div class="chatbot-name">${chatbot.name}</div>
                            <div class="chatbot-stats">
                                <span><i class="fas fa-comments me-1"></i>${formatNumber(chatbot.message_count)} messages</span> • 
                                <span><i class="fas fa-users me-1"></i>${formatNumber(chatbot.user_count)} users</span>
                            </div>
                        </div>
                        <a href="/analytics/chatbot/${chatbot.id}/" class="btn btn-sm btn-outline-primary">Details</a>
                    </div>
                    <div class="progress mt-2" style="height: 6px;">
                        <div class="progress-bar ${getProgressBarClass(chatbot.satisfaction_rate)}" role="progressbar" 
                             style="width: ${chatbot.satisfaction_rate}%;" 
                             aria-valuenow="${chatbot.satisfaction_rate}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                `;
                chatbotList.appendChild(chatbotItem);
            });
        })
        .catch(error => console.error('Error loading chatbot performance data:', error));
}

/**
 * Load recent activity data
 */
function loadRecentActivityData() {
    fetch('/analytics/api/recent-activity/')
        .then(response => response.json())
        .then(data => {
            const activityList = document.querySelector('.list-group');
            activityList.innerHTML = '';
            
            data.activities.forEach(activity => {
                const activityItem = document.createElement('div');
                activityItem.className = 'list-group-item border-0 py-3';
                activityItem.innerHTML = `
                    <div class="d-flex">
                        <div class="activity-icon bg-${activity.icon_bg} text-white rounded-circle p-2 me-3">
                            <i class="fas fa-${activity.icon}"></i>
                        </div>
                        <div>
                            <p class="mb-1">${activity.message}</p>
                            <small class="text-muted"><i class="far fa-clock me-1"></i>${activity.time}</small>
                        </div>
                    </div>
                `;
                activityList.appendChild(activityItem);
            });
        })
        .catch(error => console.error('Error loading recent activity data:', error));
}

/**
 * Set up refresh buttons for charts
 */
function setupRefreshButtons() {
    // Message Volume Chart refresh
    document.getElementById('refreshMessageVolumeChart').addEventListener('click', function() {
        const period = getSelectedTimePeriod();
        loadMessageVolumeData(period);
    });
    
    // User Engagement Chart refresh
    document.getElementById('refreshUserEngagementChart').addEventListener('click', function() {
        const period = getSelectedTimePeriod();
        loadUserEngagementData(period);
    });
    
    // Channel Distribution Chart refresh
    document.getElementById('refreshChannelDistributionChart').addEventListener('click', function() {
        const period = getSelectedTimePeriod();
        loadChannelDistributionData(period);
    });
    
    // Recent Activity refresh
    document.getElementById('refreshRecentActivity').addEventListener('click', function() {
        loadRecentActivityData();
    });
}

/**
 * Get the currently selected time period
 */
function getSelectedTimePeriod() {
    const activeButton = document.querySelector('.time-period-selector button.btn-primary');
    return activeButton ? activeButton.textContent.trim().toLowerCase() : 'all';
}

/**
 * Format number with commas for thousands
 */
function formatNumber(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Get the appropriate progress bar class based on satisfaction rate
 */
function getProgressBarClass(rate) {
    if (rate >= 85) {
        return 'bg-success';
    } else if (rate >= 70) {
        return 'bg-warning';
    } else {
        return 'bg-danger';
    }
}
