/* ========================================
   MAIN.JS - E-Learning LPK Yamaguchi
   All inline JavaScript extracted to external file
   ======================================== */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // LOGO IMAGE ERROR HANDLER
    // ==========================================
    
    const logoImage = document.querySelector('.logo-image');
    if (logoImage) {
        logoImage.addEventListener('error', function() {
            if (this.dataset.fallback) {
                this.src = this.dataset.fallback;
            }
            this.style.display = 'none';
        });
    }
    
    // ==========================================
    // INITIALIZE BOOTSTRAP COMPONENTS
    // ==========================================
    
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // ==========================================
    // IMAGE PREVIEW FUNCTIONS
    // ==========================================
    
    // Preview image for add/edit question
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(input => {
        if (input.id === 'image' || input.hasAttribute('data-preview')) {
            input.addEventListener('change', function() {
                previewImage(this);
            });
        }
    });
    
    // Preview for avatar input in edit profile
    const avatarInput = document.getElementById('avatar-input');
    if (avatarInput) {
        initializeAvatarCropper();
    }
    
    // ==========================================
    // CONFIRM DELETE HANDLERS
    // ==========================================
    
    // Handle all delete confirmations
    const deleteLinks = document.querySelectorAll('a[href*="delete"]');
    deleteLinks.forEach(link => {
        const href = link.getAttribute('href');
        const confirmMsg = link.getAttribute('data-confirm') || 'Apakah Anda yakin ingin menghapus?';
        
        if (href && href.includes('delete')) {
            link.addEventListener('click', function(e) {
                if (!confirm(confirmMsg)) {
                    e.preventDefault();
                    return false;
                }
            });
        }
    });
    
    // ==========================================
    // PASSWORD TOGGLE VISIBILITY
    // ==========================================
    
    const togglePassword = document.getElementById('togglePassword');
    const passwordField = document.getElementById('password');
    
    if (togglePassword && passwordField) {
        togglePassword.addEventListener('click', function() {
            const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
            
            // Toggle icon
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            }
        });
        
        // Support keyboard navigation
        togglePassword.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    }
    
    // ==========================================
    // ROLE SELECT HANDLERS
    // ==========================================
    
    // For register and edit user pages
    const roleSelect = document.getElementById('roleSelect');
    const classSelectDiv = document.getElementById('classSelectDiv');
    const classSelect = document.getElementById('classSelect');
    
    if (roleSelect && classSelectDiv) {
        roleSelect.addEventListener('change', function() {
            if (this.value === 'student') {
                classSelectDiv.style.display = 'block';
                if (classSelect) {
                    classSelect.required = false; // Optional for students
                }
            } else {
                classSelectDiv.style.display = 'none';
                if (classSelect) {
                    classSelect.required = false;
                    classSelect.value = '';
                }
            }
        });
        
        // Trigger on page load
        roleSelect.dispatchEvent(new Event('change'));
    }
    
    // ==========================================
    // FILE NAME PREVIEW
    // ==========================================
    
    // For certificate creation and task uploads
    const fileInputWithPreview = document.querySelectorAll('input[type="file"][data-show-filename]');
    fileInputWithPreview.forEach(input => {
        input.addEventListener('change', function() {
            if (this.id === 'file' || this.id === 'submission_file') {
                showFileName(this);
            } else {
                previewFileName(this);
            }
        });
    });
    
    // ==========================================
    // FORM VALIDATION
    // ==========================================
    
    // Password match validation for reset password
    const resetPasswordForm = document.querySelector('form[action*="reset_password"]');
    if (resetPasswordForm) {
        resetPasswordForm.addEventListener('submit', function(e) {
            const password = this.querySelector('input[name="new_password"]');
            const confirm = this.querySelector('input[name="confirm_password"]');
            
            if (password && confirm && password.value !== confirm.value) {
                e.preventDefault();
                alert('Konfirmasi password tidak cocok!');
                return false;
            }
        });
    }
    
    // ==========================================
    // QUIZ CREATION FORM
    // ==========================================
    
    const createQuizForm = document.getElementById('createQuizForm');
    if (createQuizForm) {
        createQuizForm.addEventListener('submit', function(e) {
            const titleInput = document.getElementById('title');
            const submitBtn = this.querySelector('button[type="submit"]');
            
            if (titleInput && titleInput.value.trim() === '') {
                e.preventDefault();
                alert('⚠️ Judul kuis tidak boleh kosong!');
                titleInput.focus();
                return;
            }
            
            // Show loading state
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Membuat kuis dan menyiapkan halaman pertanyaan...';
                submitBtn.classList.add('loading');
            }
        });
    }
    
    // ==========================================
    // ADMIN CLASS EDIT FORM
    // ==========================================
    
    const editClassForm = document.getElementById('editClassForm');
    if (editClassForm) {
        const descriptionTextarea = document.getElementById('description');
        const charCountSpan = document.getElementById('charCount');
        
        if (descriptionTextarea && charCountSpan) {
            function updateCharCount() {
                const count = descriptionTextarea.value.length;
                charCountSpan.textContent = count;
                
                // Change color if approaching limit
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
        }
        
        // Form validation
        editClassForm.addEventListener('submit', function(e) {
            const name = document.getElementById('name');
            
            if (name && !name.value.trim()) {
                e.preventDefault();
                alert('Nama kelas harus diisi!');
                name.focus();
                return false;
            }
            
            // Confirmation
            if (!confirm('Apakah Anda yakin ingin menyimpan perubahan kelas ini?')) {
                e.preventDefault();
                return false;
            }
        });
        
        // Auto-focus on first input
        const nameInput = document.getElementById('name');
        if (nameInput) {
            nameInput.focus();
        }
        
        // Prevent accidental navigation
        let formModified = false;
        const formInputs = editClassForm.querySelectorAll('input, textarea');
        
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
        editClassForm.addEventListener('submit', () => {
            formModified = false;
        });
        
        // Smooth scroll to top on load
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    // ==========================================
    // QUIZ SUBMIT CONFIRMATION
    // ==========================================
    
    const quizSubmitButtons = document.querySelectorAll('button[type="submit"][data-quiz-submit]');
    quizSubmitButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Yakin ingin submit kuis ini?')) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // ==========================================
    // SORT SELECT AUTO SUBMIT
    // ==========================================
    
    const sortSelects = document.querySelectorAll('select[name="sort"]');
    sortSelects.forEach(select => {
        select.addEventListener('change', function() {
            if (this.form) {
                this.form.submit();
            }
        });
    });
    
    // ==========================================
    // INPUT SANITIZATION
    // ==========================================
    
    // Sanitize input to prevent XSS (basic sanitization)
    function sanitizeInput(input) {
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }
    
    // Apply to all text inputs on form submit
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const textInputs = this.querySelectorAll('input[type="text"], textarea');
            textInputs.forEach(input => {
                if (input.value) {
                    input.value = sanitizeInput(input.value);
                }
            });
        });
    });
    
}); // End of DOMContentLoaded

// ==========================================
// GLOBAL FUNCTIONS (callable from HTML if needed during migration)
// ==========================================

/**
 * Preview image before upload
 * @param {HTMLInputElement} input - File input element
 */
function previewImage(input) {
    const preview = document.getElementById('preview');
    const previewDiv = document.getElementById('imagePreview');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            if (preview) preview.src = e.target.result;
            if (previewDiv) previewDiv.style.display = 'block';
        }
        
        reader.readAsDataURL(input.files[0]);
    } else {
        if (previewDiv) previewDiv.style.display = 'none';
    }
}

/**
 * Open image in modal
 * @param {string} src - Image source URL
 */
function openImageModal(src) {
    const modalImage = document.getElementById('modalImage');
    if (modalImage) {
        modalImage.src = src;
        const modal = new bootstrap.Modal(document.getElementById('imageModal'));
        modal.show();
    }
}

/**
 * Show file name and size for task/certificate uploads
 * @param {HTMLInputElement} input - File input element
 */
function showFileName(input) {
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    if (!fileNameDisplay) return;
    
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

/**
 * Preview file name for certificate creation
 * @param {HTMLInputElement} input - File input element
 */
function previewFileName(input) {
    const preview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
        
        if (fileSize > 4) {
            alert('Ukuran file terlalu besar! Maksimal 4MB.');
            input.value = '';
            if (preview) preview.style.display = 'none';
            return;
        }
        
        if (fileName) {
            fileName.textContent = file.name + ' (' + fileSize + ' MB)';
        }
        if (preview) {
            preview.style.display = 'block';
        }
    } else {
        if (preview) preview.style.display = 'none';
    }
}

/**
 * Basic input sanitization
 * @param {string} input - Input string to sanitize
 * @returns {string} Sanitized string
 */
function sanitizeInput(input) {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
}

// ==========================================
// AVATAR CROPPER INITIALIZATION
// ==========================================

function initializeAvatarCropper() {
    let cropper;
    let scaleX = 1;
    let scaleY = 1;
    
    const avatarInput = document.getElementById('avatar-input');
    const imageToCrop = document.getElementById('image-to-crop');
    const avatarModalElement = document.getElementById('avatarModal');
    const cropButton = document.getElementById('cropButton');
    const avatarData = document.getElementById('avatar-data');
    const currentAvatar = document.getElementById('current-avatar');
    const previewContainer = document.getElementById('preview-container');
    const avatarPreview = document.getElementById('avatar-preview');
    const profileForm = document.getElementById('profileForm');
    
    // Rotation buttons
    const rotateLeft = document.getElementById('rotateLeft');
    const rotateRight = document.getElementById('rotateRight');
    const flipHorizontal = document.getElementById('flipHorizontal');
    const flipVertical = document.getElementById('flipVertical');
    
    if (!avatarInput || !imageToCrop || !avatarModalElement) {
        return; // Exit if elements don't exist
    }
    
    const avatarModal = new bootstrap.Modal(avatarModalElement);
    
    // When user selects a file
    avatarInput.addEventListener('change', function(e) {
        const files = e.target.files;
        
        if (files && files.length > 0) {
            const file = files[0];
            
            // Validate file size (max 4MB)
            if (file.size > 4 * 1024 * 1024) {
                alert('Ukuran file terlalu besar! Maksimal 4MB.');
                avatarInput.value = '';
                return;
            }
            
            // Validate file type
            if (!file.type.match('image.*')) {
                alert('File harus berupa gambar!');
                avatarInput.value = '';
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = function(event) {
                imageToCrop.src = event.target.result;
                avatarModal.show();
                
                // Destroy old cropper if exists
                if (cropper) {
                    cropper.destroy();
                }
                
                // Reset scale
                scaleX = 1;
                scaleY = 1;
                
                // Initialize cropper with 3:4 ratio
                cropper = new Cropper(imageToCrop, {
                    aspectRatio: 3 / 4, // 3:4 ratio
                    viewMode: 2,
                    dragMode: 'move',
                    autoCropArea: 1,
                    restore: false,
                    guides: true,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                    minContainerWidth: 300,
                    minContainerHeight: 400,
                });
            };
            
            reader.readAsDataURL(file);
        }
    });
    
    // Rotate Left
    if (rotateLeft) {
        rotateLeft.addEventListener('click', function() {
            if (cropper) {
                cropper.rotate(-45);
            }
        });
    }
    
    // Rotate Right
    if (rotateRight) {
        rotateRight.addEventListener('click', function() {
            if (cropper) {
                cropper.rotate(45);
            }
        });
    }
    
    // Flip Horizontal
    if (flipHorizontal) {
        flipHorizontal.addEventListener('click', function() {
            if (cropper) {
                scaleX = scaleX === 1 ? -1 : 1;
                cropper.scaleX(scaleX);
            }
        });
    }
    
    // Flip Vertical
    if (flipVertical) {
        flipVertical.addEventListener('click', function() {
            if (cropper) {
                scaleY = scaleY === 1 ? -1 : 1;
                cropper.scaleY(scaleY);
            }
        });
    }
    
    // When user clicks "Crop & Use"
    if (cropButton) {
        cropButton.addEventListener('click', function() {
            if (cropper) {
                // Get cropped canvas with optimal size (3:4 ratio)
                const canvas = cropper.getCroppedCanvas({
                    width: 600,  // 3:4 ratio (600x800)
                    height: 800,
                    imageSmoothingEnabled: true,
                    imageSmoothingQuality: 'high',
                });
                
                // Convert canvas to base64 (JPEG with quality 0.9)
                const base64Image = canvas.toDataURL('image/jpeg', 0.9);
                
                // Save to hidden input
                if (avatarData) avatarData.value = base64Image;
                
                // Update preview
                if (avatarPreview) avatarPreview.src = base64Image;
                if (previewContainer) previewContainer.style.display = 'block';
                
                // Update current avatar display
                if (currentAvatar) currentAvatar.src = base64Image;
                
                // Close modal
                avatarModal.hide();
                
                // Show success message
                const card = document.querySelector('.card');
                if (card) {
                    const successMsg = document.createElement('div');
                    successMsg.className = 'alert alert-success alert-dismissible fade show mt-3';
                    successMsg.innerHTML = `
                        <strong>Berhasil!</strong> Foto profil telah di-crop. Klik "Simpan Perubahan" untuk menyimpan.
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    card.insertBefore(successMsg, card.querySelector('form'));
                    
                    // Auto dismiss after 5 seconds
                    setTimeout(() => {
                        successMsg.remove();
                    }, 5000);
                }
            }
        });
    }
    
    // Clean up when modal is closed
    avatarModalElement.addEventListener('hidden.bs.modal', function() {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        // Reset input if user cancelled
        if (avatarData && !avatarData.value) {
            avatarInput.value = '';
        }
    });
    
    // Prevent form submission if there's an error
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            // Optional: Add validation here
            console.log('Form submitted with avatar data:', avatarData && avatarData.value ? 'Yes' : 'No');
        });
    }
}
