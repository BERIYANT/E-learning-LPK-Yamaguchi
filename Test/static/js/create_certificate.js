// Preview nama file yang dipilih
function previewFileName(input) {
    const preview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
        
        if (fileSize > 4) {
            alert('Ukuran file terlalu besar! Maksimal 4MB.');
            input.value = '';
            preview.style.display = 'none';
            return;
        }
        
        fileName.textContent = file.name + ' (' + fileSize + ' MB)';
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
}

// Initialize Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});