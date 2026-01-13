
// Function to safely extract JSON data from the script tags
function getJsonData(id) {
    const element = document.getElementById(id);
    // Safely parse or return empty array on failure/missing
    try {
        return element ? JSON.parse(element.textContent) : [];
    } catch (e) {
        console.error("Could not parse JSON for element:", id, e);
        return [];
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Retrieve data safely
    const trendLabels = getJsonData('trend-labels-data');
    const trendData = getJsonData('trend-data');
    const genreLabels = getJsonData('genre-labels-data');
    const genreData = getJsonData('genre-data');


    // 1. Borrowing Trends Chart
    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        new Chart(trendCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: trendLabels,
                datasets: [{
                    label: 'Books Issued',
                    data: trendData,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { borderDash: [5, 5] },
                        ticks: {
                            // Ensure only whole numbers are displayed
                            callback: function (value, index, values) {
                                if (value % 1 === 0) {
                                    return value;
                                }
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Genre Distribution Chart
    const genreCtx = document.getElementById('genreChart');
    if (genreCtx) {
        new Chart(genreCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: genreLabels,
                datasets: [{
                    data: genreData,
                    backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
});
