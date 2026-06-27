document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on the dashboard page
    const salesChartCanvas = document.getElementById('salesTrendChart');
    if (!salesChartCanvas) return;
    
    // Fetch chart data from backend API
    fetch('/api/dashboard/charts')
        .then(response => response.json())
        .then(data => {
            initCharts(data);
        })
        .catch(err => console.error('Error fetching chart data:', err));
});

function initCharts(data) {
    // 1. Monthly Sales Trend (Line Chart)
    const ctxSales = document.getElementById('salesTrendChart').getContext('2d');
    new Chart(ctxSales, {
        type: 'line',
        data: {
            labels: data.monthlySales.labels,
            datasets: [{
                label: 'Monthly Sales ($)',
                data: data.monthlySales.data,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#6366f1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                    ticks: { callback: value => '$' + value }
                },
                x: { grid: { display: false } }
            }
        }
    });

    // 2. Top Product Sales (Bar Chart)
    const ctxProd = document.getElementById('productSalesChart').getContext('2d');
    new Chart(ctxProd, {
        type: 'bar',
        data: {
            labels: data.productSales.labels,
            datasets: [{
                label: 'Total Revenue ($)',
                data: data.productSales.data,
                backgroundColor: 'linear-gradient(to right, #10b981, #059669)',
                borderRadius: 8,
                backgroundColor: [
                    'rgba(16, 185, 129, 0.85)',
                    'rgba(99, 102, 241, 0.85)',
                    'rgba(245, 158, 11, 0.85)',
                    'rgba(239, 68, 68, 0.85)',
                    'rgba(168, 85, 247, 0.85)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });

    // 3. Category Split (Doughnut Chart)
    const ctxCat = document.getElementById('categoryShareChart').getContext('2d');
    new Chart(ctxCat, {
        type: 'doughnut',
        data: {
            labels: data.categoryShare.labels,
            datasets: [{
                data: data.categoryShare.data,
                backgroundColor: [
                    '#6366f1',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444',
                    '#a855f7'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            },
            cutout: '70%'
        }
    });

    // 4. Inventory Alerts (Bar Chart comparing stock levels and reorder limits)
    const ctxInv = document.getElementById('inventoryAlertsChart').getContext('2d');
    new Chart(ctxInv, {
        type: 'bar',
        data: {
            labels: data.inventoryAlerts.labels,
            datasets: [
                {
                    label: 'Current Stock',
                    data: data.inventoryAlerts.stock,
                    backgroundColor: 'rgba(99, 102, 241, 0.8)',
                    borderRadius: 6
                },
                {
                    label: 'Reorder Point',
                    data: data.inventoryAlerts.reorder,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });
}
