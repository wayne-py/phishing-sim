document.addEventListener('DOMContentLoaded', function() {
    // Dashboard charts
    const campaignStatsCanvas = document.getElementById('campaignStatsChart');
    if (campaignStatsCanvas) {
        const sentCount = parseInt(campaignStatsCanvas.getAttribute('data-sent'));
        const openedCount = parseInt(campaignStatsCanvas.getAttribute('data-opened'));
        const clickedCount = parseInt(campaignStatsCanvas.getAttribute('data-clicked'));
        
        new Chart(campaignStatsCanvas, {
            type: 'bar',
            data: {
                labels: ['Sent', 'Opened', 'Clicked'],
                datasets: [{
                    label: 'Email Status',
                    data: [sentCount, openedCount, clickedCount],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',  // blue
                        'rgba(255, 206, 86, 0.8)',  // yellow
                        'rgba(255, 99, 132, 0.8)'   // red
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        precision: 0
                    }
                }
            }
        });
    }
    
    // Campaign report charts
    const campaignReportCanvas = document.getElementById('campaignReportChart');
    if (campaignReportCanvas) {
        const emailsSent = parseInt(campaignReportCanvas.getAttribute('data-sent'));
        const emailsOpened = parseInt(campaignReportCanvas.getAttribute('data-opened'));
        const linksClicked = parseInt(campaignReportCanvas.getAttribute('data-clicked'));
        
        new Chart(campaignReportCanvas, {
            type: 'doughnut',
            data: {
                labels: [
                    'Not Opened', 
                    'Opened (No Click)', 
                    'Clicked Link'
                ],
                datasets: [{
                    data: [
                        emailsSent - emailsOpened, 
                        emailsOpened - linksClicked, 
                        linksClicked
                    ],
                    backgroundColor: [
                        'rgba(108, 117, 125, 0.8)',  // gray
                        'rgba(255, 193, 7, 0.8)',    // warning
                        'rgba(220, 53, 69, 0.8)'     // danger
                    ],
                    borderColor: [
                        'rgba(108, 117, 125, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(220, 53, 69, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Timeline chart for campaign report
    const timelineCanvas = document.getElementById('timelineChart');
    if (timelineCanvas) {
        const sentData = JSON.parse(timelineCanvas.getAttribute('data-sent'));
        const openedData = JSON.parse(timelineCanvas.getAttribute('data-opened'));
        const clickedData = JSON.parse(timelineCanvas.getAttribute('data-clicked'));
        
        new Chart(timelineCanvas, {
            type: 'line',
            data: {
                labels: sentData.map(item => item.date),
                datasets: [
                    {
                        label: 'Sent',
                        data: sentData.map(item => item.count),
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1,
                        fill: true
                    },
                    {
                        label: 'Opened',
                        data: openedData.map(item => item.count),
                        borderColor: 'rgba(255, 206, 86, 1)',
                        backgroundColor: 'rgba(255, 206, 86, 0.2)',
                        tension: 0.1,
                        fill: true
                    },
                    {
                        label: 'Clicked',
                        data: clickedData.map(item => item.count),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        precision: 0
                    }
                }
            }
        });
    }
});
