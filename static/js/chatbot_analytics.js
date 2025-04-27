/**
 * Chatbot Analytics JavaScript
 * Handles all chart rendering and interactive functionality for the chatbot analytics page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts
    initMessageVolumeChart();
    initUserEngagementChart();
    initResponseTimeChart();
    initSatisfactionChart();
    initSentimentChart();
    
    // Set up time period selector
    setupTimePeriodSelector();
    
    // Set up export buttons
    setupExportButtons();
    
    // Set up refresh buttons
    setupRefreshButtons();
});

/**
 * Initialize Message Volume Chart
 */
function initMessageVolumeChart() {
    const messageVolumeCtx = document.getElementById('messageVolumeChart').getContext('2d');
    window.messageVolumeChart = new Chart(messageVolumeCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Messages',
                data: [520, 480, 750, 620, 830, 580, 450],
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
 * Initialize User Engagement Chart
 */
function initUserEngagementChart() {
    const userEngagementCtx = document.getElementById('userEngagementChart').getContext('2d');
    window.userEngagementChart = new Chart(userEngagementCtx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [
                {
                    label: 'Active Users',
                    data: [120, 150, 180, 170, 160, 140, 130],
                    backgroundColor: 'rgba(45, 204, 167, 0.7)',
                    borderColor: 'rgba(45, 204, 167, 1)',
                    borderWidth: 1
                },
                {
                    label: 'New Users',
                    data: [45, 60, 75, 65, 55, 40, 35],
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
 * Initialize Response Time Chart
 */
function initResponseTimeChart() {
    const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
    window.responseTimeChart = new Chart(responseTimeCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Avg. Response Time (sec)',
                data: [1.2, 1.5, 1.3, 1.1, 1.4, 1.2, 1.0],
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                borderColor: 'rgba(255, 193, 7, 1)',
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
                    callbacks: {
                        label: function(context) {
                            return `${context.raw} seconds`;
                        }
                    }
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
 * Initialize Satisfaction Chart
 */
function initSatisfactionChart() {
    const satisfactionCtx = document.getElementById('satisfactionChart').getContext('2d');
    window.satisfactionChart = new Chart(satisfactionCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'User Satisfaction (%)',
                data: [85, 82, 88, 90, 87, 89, 91],
                backgroundColor: 'rgba(23, 162, 184, 0.1)',
                borderColor: 'rgba(23, 162, 184, 1)',
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
                    callbacks: {
                        label: function(context) {
                            return `${context.raw}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 50,
                    max: 100,
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
 * Initialize Sentiment Chart
 */
function initSentimentChart() {
    const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
    window.sentimentChart = new Chart(sentimentCtx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [68, 24, 8],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(108, 117, 125, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(108, 117, 125, 1)',
                    'rgba(220, 53, 69, 1)'
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
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
}

/**
 * Set up time period selector
 */
function setupTimePeriodSelector() {
    const timePeriodButtons = document.querySelectorAll('#time-period-selector button');
    
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
            
            // Update charts based on selected time period
            updateChartsForTimePeriod(this.getAttribute('data-period'));
        });
    });
}

/**
 * Update charts based on selected time period
 */
function updateChartsForTimePeriod(period) {
    // In a real application, this would fetch data from the server
    // For demo purposes, we'll just simulate different data for different periods
    
    let labels = [];
    let messageData = [];
    let activeUserData = [];
    let newUserData = [];
    let responseTimeData = [];
    let satisfactionData = [];
    let sentimentData = [];
    
    switch(period) {
        case 'today':
            labels = ['9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm', '4pm', '5pm'];
            messageData = [45, 60, 75, 90, 120, 105, 85, 70, 50];
            activeUserData = [15, 22, 28, 35, 42, 38, 30, 25, 18];
            newUserData = [5, 8, 10, 12, 15, 11, 9, 7, 4];
            responseTimeData = [1.0, 1.2, 1.5, 1.8, 1.6, 1.4, 1.3, 1.1, 1.0];
            satisfactionData = [88, 87, 86, 85, 84, 86, 87, 89, 90];
            sentimentData = [70, 22, 8];
            break;
        case 'week':
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            messageData = [520, 480, 750, 620, 830, 580, 450];
            activeUserData = [120, 150, 180, 170, 160, 140, 130];
            newUserData = [45, 60, 75, 65, 55, 40, 35];
            responseTimeData = [1.2, 1.5, 1.3, 1.1, 1.4, 1.2, 1.0];
            satisfactionData = [85, 82, 88, 90, 87, 89, 91];
            sentimentData = [68, 24, 8];
            break;
        case 'month':
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
            messageData = [3200, 3800, 4100, 3600];
            activeUserData = [850, 920, 980, 890];
            newUserData = [320, 280, 250, 310];
            responseTimeData = [1.3, 1.2, 1.1, 1.0];
            satisfactionData = [84, 86, 89, 92];
            sentimentData = [65, 27, 8];
            break;
        case 'year':
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            messageData = [12000, 14500, 16800, 18200, 19500, 21000, 23000, 24500, 26000, 27500, 29000, 31000];
            activeUserData = [3200, 3500, 3800, 4100, 4300, 4600, 4800, 5100, 5400, 5700, 6000, 6300];
            newUserData = [1200, 1100, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200];
            responseTimeData = [1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.8, 0.7, 0.7, 0.6];
            satisfactionData = [80, 82, 83, 85, 86, 87, 88, 89, 90, 91, 92, 93];
            sentimentData = [72, 20, 8];
            break;
    }
    
    // Update message volume chart
    window.messageVolumeChart.data.labels = labels;
    window.messageVolumeChart.data.datasets[0].data = messageData;
    window.messageVolumeChart.update();
    
    // Update user engagement chart
    window.userEngagementChart.data.labels = labels;
    window.userEngagementChart.data.datasets[0].data = activeUserData;
    window.userEngagementChart.data.datasets[1].data = newUserData;
    window.userEngagementChart.update();
    
    // Update response time chart
    window.responseTimeChart.data.labels = labels;
    window.responseTimeChart.data.datasets[0].data = responseTimeData;
    window.responseTimeChart.update();
    
    // Update satisfaction chart
    window.satisfactionChart.data.labels = labels;
    window.satisfactionChart.data.datasets[0].data = satisfactionData;
    window.satisfactionChart.update();
    
    // Update sentiment chart
    window.sentimentChart.data.datasets[0].data = sentimentData;
    window.sentimentChart.update();
}

/**
 * Set up export buttons
 */
function setupExportButtons() {
    document.getElementById('export-pdf').addEventListener('click', function(e) {
        e.preventDefault();
        alert('Exporting PDF report...');
        // In a real application, this would trigger a server-side PDF generation
    });
    
    document.getElementById('export-excel').addEventListener('click', function(e) {
        e.preventDefault();
        alert('Exporting Excel report...');
        // In a real application, this would trigger a server-side Excel generation
    });
    
    document.getElementById('export-csv').addEventListener('click', function(e) {
        e.preventDefault();
        alert('Exporting CSV report...');
        // In a real application, this would trigger a server-side CSV generation
    });
}

/**
 * Set up refresh buttons for charts
 */
function setupRefreshButtons() {
    document.getElementById('refreshMessageVolumeChart').addEventListener('click', function() {
        const newData = generateRandomData(window.messageVolumeChart.data.labels.length, 400, 900);
        window.messageVolumeChart.data.datasets[0].data = newData;
        window.messageVolumeChart.update();
    });
    
    document.getElementById('refreshUserEngagementChart').addEventListener('click', function() {
        const newActiveUsers = generateRandomData(window.userEngagementChart.data.labels.length, 100, 200);
        const newNewUsers = generateRandomData(window.userEngagementChart.data.labels.length, 30, 80);
        window.userEngagementChart.data.datasets[0].data = newActiveUsers;
        window.userEngagementChart.data.datasets[1].data = newNewUsers;
        window.userEngagementChart.update();
    });
    
    document.getElementById('refreshResponseTimeChart').addEventListener('click', function() {
        const newData = generateRandomData(window.responseTimeChart.data.labels.length, 0.7, 2.0, 1);
        window.responseTimeChart.data.datasets[0].data = newData;
        window.responseTimeChart.update();
    });
    
    document.getElementById('refreshSatisfactionChart').addEventListener('click', function() {
        const newData = generateRandomData(window.satisfactionChart.data.labels.length, 75, 95);
        window.satisfactionChart.data.datasets[0].data = newData;
        window.satisfactionChart.update();
    });
}

/**
 * Generate random data for chart refreshes
 */
function generateRandomData(length, min, max, decimals = 0) {
    return Array.from({length: length}, () => {
        const value = Math.random() * (max - min) + min;
        return decimals > 0 ? parseFloat(value.toFixed(decimals)) : Math.floor(value);
    });
}
