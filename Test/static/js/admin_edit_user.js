document.getElementById('roleSelect').addEventListener('change', function() {
    const classDiv = document.getElementById('classSelectDiv');
    const classSelect = document.getElementById('classSelect');
    
    if (this.value === 'student') {
        classDiv.style.display = 'block';
    } else {
        classDiv.style.display = 'none';
        classSelect.value = '';
    }
});

// Trigger on page load
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('roleSelect').dispatchEvent(new Event('change'));
});