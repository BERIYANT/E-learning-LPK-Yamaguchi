function showFileName(input) {
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    if (input.files && input.files[0]) {
        const fileName = input.files[0].name;
        const fileSize = (input.files[0].size / 1024 / 1024).toFixed(2);
        if (fileSize > 4) {
            fileNameDisplay.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong>File terlalu besar!</strong> Ukuran: ${fileSize} MB (Maksimal 4 MB)
                </div>`;
            input.value = '';
        } else {
            fileNameDisplay.innerHTML = `
                <div class="alert alert-success mb-0">
                    <i class="bi bi-file-earmark-check"></i>
                    <strong>File dipilih:</strong> ${fileName} (${fileSize} MB)
                </div>`;
        }
    }
}