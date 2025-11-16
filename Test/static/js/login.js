(function() {
    'use strict';
    
    document.addEventListener("DOMContentLoaded", function() {
        const togglePassword = document.getElementById("togglePassword");
        const passwordInput = document.getElementById("password");
        const icon = togglePassword ? togglePassword.querySelector("i") : null;
        const loginForm = document.getElementById("loginForm");
        const submitBtn = document.getElementById("submitBtn");
        const usernameInput = document.getElementById("username");
        
        // ✅ Toggle Password Visibility
        if (togglePassword && passwordInput && icon) {
            togglePassword.addEventListener("click", function() {
                const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
                passwordInput.setAttribute("type", type);
                icon.classList.toggle("fa-eye");
                icon.classList.toggle("fa-eye-slash");
            });
            
            // Keyboard accessibility
            togglePassword.addEventListener("keypress", function(e) {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    togglePassword.click();
                }
            });
        }
        
        // ✅ SECURITY: Input Sanitization
        function sanitizeInput(input) {
            if (!input) return input;
            // Remove HTML tags - multiple passes to prevent incomplete sanitization
            let sanitized = input;
            let previousLength;
            do {
                previousLength = sanitized.length;
                sanitized = sanitized.replace(/<[^>]*>/g, '');
            } while (sanitized.length !== previousLength);
            return sanitized;
        }
        
        // ✅ SECURITY: Form Validation & Rate Limiting
        let loginAttempts = parseInt(localStorage.getItem('loginAttempts') || '0');
        let lastAttempt = parseInt(localStorage.getItem('lastLoginAttempt') || '0');
        const MAX_ATTEMPTS = 5;
        const LOCKOUT_TIME = 5 * 60 * 1000; // 5 menit
        
        // Check if user is locked out
        function isLockedOut() {
            const now = Date.now();
            if (loginAttempts >= MAX_ATTEMPTS) {
                if (now - lastAttempt < LOCKOUT_TIME) {
                    return true;
                } else {
                    // Reset after lockout period
                    loginAttempts = 0;
                    localStorage.setItem('loginAttempts', '0');
                    return false;
                }
            }
            return false;
        }
        
        // Show lockout warning
        if (isLockedOut()) {
            const warning = document.getElementById('rateLimitWarning');
            if (warning) {
                warning.classList.remove('d-none');
            }
            if (submitBtn) {
                submitBtn.disabled = true;
            }
            
            // Enable after lockout period
            setTimeout(function() {
                loginAttempts = 0;
                localStorage.setItem('loginAttempts', '0');
                if (warning) {
                    warning.classList.add('d-none');
                }
                if (submitBtn) {
                    submitBtn.disabled = false;
                }
            }, LOCKOUT_TIME - (Date.now() - lastAttempt));
        }
        
        // ✅ Form Submit Handler
        if (loginForm) {
            loginForm.addEventListener("submit", function(e) {
                // Check lockout
                if (isLockedOut()) {
                    e.preventDefault();
                    alert("Terlalu banyak percobaan login gagal. Silakan tunggu 5 menit.");
                    return false;
                }
                
                // Sanitize inputs
                if (usernameInput) {
                    usernameInput.value = sanitizeInput(usernameInput.value.trim());
                }
                
                // ✅ Check honeypot
                const honeypot = document.querySelector('input[name="website"]');
                if (honeypot && honeypot.value) {
                    e.preventDefault();
                    console.warn('Bot detected');
                    return false;
                }
                
                // Validate inputs
                if (usernameInput && !usernameInput.value.trim()) {
                    e.preventDefault();
                    alert("Username tidak boleh kosong");
                    usernameInput.focus();
                    return false;
                }
                
                if (passwordInput && passwordInput.value.length < 6) {
                    e.preventDefault();
                    alert("Password minimal 6 karakter");
                    passwordInput.focus();
                    return false;
                }
                
                // Disable button to prevent double submit
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';
                }
                
                // Increment attempt counter
                loginAttempts++;
                lastAttempt = Date.now();
                localStorage.setItem('loginAttempts', loginAttempts.toString());
                localStorage.setItem('lastLoginAttempt', lastAttempt.toString());
                
                return true;
            });
        }
        
        // ✅ SECURITY: Clear sensitive data on page unload
        window.addEventListener('beforeunload', function() {
            if (passwordInput) {
                passwordInput.value = '';
            }
        });
        
        // ✅ SECURITY: Prevent password paste (optional - dapat di-enable jika diperlukan)
        // passwordInput.addEventListener('paste', function(e) {
        //     e.preventDefault();
        //     alert('Paste tidak diizinkan untuk keamanan');
        // });
        
        // ✅ Reset attempts on successful page load (if redirected from successful login)
        if (window.location.search.includes('success')) {
            localStorage.removeItem('loginAttempts');
            localStorage.removeItem('lastLoginAttempt');
        }
    });
})();