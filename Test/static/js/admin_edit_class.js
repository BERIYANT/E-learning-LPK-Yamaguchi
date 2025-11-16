// Character counter untuk description
    const descriptionTextarea = document.getElementById('description');
    const charCountSpan = document.getElementById('charCount');
    
    function updateCharCount() {
        const count = descriptionTextarea.value.length;
        charCountSpan.textContent = count;
        
        // Ubah warna jika mendekati limit
        if (count > 900) {
            charCountSpan.style.color = '#dc3545';
            charCountSpan.style.fontWeight = 'bold';
        } else if (count > 800) {
            charCountSpan.style.color = '#ffc107';
            charCountSpan.style.fontWeight = '600';
        } else {
            charCountSpan.style.color = '#6c757d';
            charCountSpan.style.fontWeight = 'normal';
        }
    }
    
    // Update on page load
    updateCharCount();
    
    // Update on input
    descriptionTextarea.addEventListener('input', updateCharCount);

    // Form validation
    document.getElementById('editClassForm').addEventListener('submit', function(e) {
        const name = document.getElementById('name').value.trim();
        
        if (!name) {
            e.preventDefault();
            alert('Nama kelas harus diisi!');
            document.getElementById('name').focus();
            return false;
        }
        
        // Confirmation
        if (!confirm('Apakah Anda yakin ingin menyimpan perubahan kelas ini?')) {
            e.preventDefault();
            return false;
        }
    });

    // Auto-focus on first input
    document.getElementById('name').focus();

    // Prevent accidental navigation
    let formModified = false;
    const formInputs = document.querySelectorAll('#editClassForm input, #editClassForm textarea');
    
    formInputs.forEach(input => {
        input.addEventListener('change', () => {
            formModified = true;
        });
    });

    window.addEventListener('beforeunload', (e) => {
        if (formModified) {
            e.preventDefault();
            e.returnValue = '';
        }
    });

    // Reset flag on form submit
    document.getElementById('editClassForm').addEventListener('submit', () => {
        formModified = false;
    });

    // Smooth scroll to top on load
    window.scrollTo({ top: 0, behavior: 'smooth' });