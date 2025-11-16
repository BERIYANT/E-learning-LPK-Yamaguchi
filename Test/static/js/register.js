document.getElementById('roleSelect').addEventListener('change', function() {
    const classDiv = document.getElementById('classSelectDiv');
    const classSelect = document.getElementById('classSelect');
    
    if (this.value === 'student') {
        classDiv.style.display = 'block';
        classSelect.required = false; // Opsional untuk siswa
    } else {
        classDiv.style.display = 'none';
        classSelect.required = false;
        classSelect.value = '';
    }
});

// Trigger on page load
document.getElementById('roleSelect').dispatchEvent(new Event('change'));