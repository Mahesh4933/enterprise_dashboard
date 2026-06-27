// Dynamic theme switching
document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Toggle icon
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                icon.className = newTheme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
            }
        });
        
        // Restore theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        const icon = themeToggleBtn.querySelector('i');
        if (icon) {
            icon.className = savedTheme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
    }
});

// View Sales Order details in modal via AJAX
function viewOrderDetails(orderId) {
    fetch(`/sales/api/order-details/${orderId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('modalOrderCode').innerText = data.order_code;
            document.getElementById('modalCustomer').innerText = data.customer_name;
            document.getElementById('modalDate').innerText = data.order_date;
            document.getElementById('modalStatus').innerText = data.status;
            document.getElementById('modalTotal').innerText = '$' + data.total_amount.toFixed(2);
            
            const tbody = document.getElementById('modalItemsBody');
            tbody.innerHTML = '';
            data.items.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${item.product_name}</td>
                    <td><code>${item.sku}</code></td>
                    <td>${item.quantity}</td>
                    <td>$${item.unit_price.toFixed(2)}</td>
                    <td>$${item.total_price.toFixed(2)}</td>
                `;
                tbody.appendChild(tr);
            });
            
            const detailsModal = new bootstrap.Modal(document.getElementById('orderDetailsModal'));
            detailsModal.show();
        })
        .catch(err => console.error('Error fetching order details:', err));
}

// Predict Single Product Sale AJAX
function predictProductSale(event) {
    if (event) event.preventDefault();
    const form = document.getElementById('singlePredictForm');
    if (!form) return;
    
    const formData = new FormData(form);
    
    fetch('/predictions/predict', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Display result card
        const resultDiv = document.getElementById('predictionResult');
        resultDiv.classList.remove('d-none');
        document.getElementById('predProduct').innerText = data.product;
        document.getElementById('predQty').innerText = data.quantity;
        document.getElementById('predVal').innerText = '$' + data.prediction.toFixed(2);
        document.getElementById('predModel').innerText = data.model_used;
    })
    .catch(err => console.error('Prediction request failed:', err));
}

// Client-side quick search for tables
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    if (!table) return;
    const tr = table.getElementsByTagName('tr');
    
    for (let i = 1; i < tr.length; i++) {
        let td = tr[i].getElementsByTagName('td');
        let matched = false;
        for (let j = 0; j < td.length; j++) {
            if (td[j]) {
                const txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    matched = true;
                    break;
                }
            }
        }
        tr[i].style.display = matched ? "" : "none";
    }
}
