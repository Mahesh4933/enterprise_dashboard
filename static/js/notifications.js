function markNotificationsRead() {
    fetch('/api/notifications/read', {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            // Hide badge
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                badge.style.display = 'none';
            }
        }
    })
    .catch(err => console.error('Error marking notifications read:', err));
}
