// Validasi password match
document.querySelector('form').addEventListener('submit', function(e) {
    const password = document.querySelector('input[name="new_password"]').value;
    const confirm = document.querySelector('input[name="confirm_password"]').value;
    
    if (password !== confirm) {
        e.preventDefault();
        alert('Konfirmasi password tidak cocok!');
        return false;
    }
});