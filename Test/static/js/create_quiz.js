document.getElementById('createQuizForm').addEventListener('submit', function(e) {
    const titleInput = document.getElementById('title');
    const submitBtn = this.querySelector('button[type="submit"]');
    
    if (titleInput.value.trim() === '') {
        e.preventDefault();
        alert('⚠️ Judul kuis tidak boleh kosong!');
        titleInput.focus();
        return;
    }
    
    // Tampilkan loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Membuat kuis dan menyiapkan halaman pertanyaan...';
    
    // Optional: Tambahkan class untuk visual feedback
    submitBtn.classList.add('loading');
});