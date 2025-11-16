let cropper;
let scaleX = 1;
let scaleY = 1;

document.addEventListener('DOMContentLoaded', function() {
  const avatarInput = document.getElementById('avatar-input');
  const imageToCrop = document.getElementById('image-to-crop');
  const avatarModal = new bootstrap.Modal(document.getElementById('avatarModal'));
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
  
  // Ketika user memilih file
  avatarInput.addEventListener('change', function(e) {
    const files = e.target.files;
    
    if (files && files.length > 0) {
      const file = files[0];
      
      // Validasi ukuran file (max 4MB)
      if (file.size > 4 * 1024 * 1024) {
        alert('Ukuran file terlalu besar! Maksimal 4MB.');
        avatarInput.value = '';
        return;
      }
      
      // Validasi tipe file
      if (!file.type.match('image.*')) {
        alert('File harus berupa gambar!');
        avatarInput.value = '';
        return;
      }
      
      const reader = new FileReader();
      
      reader.onload = function(event) {
        imageToCrop.src = event.target.result;
        avatarModal.show();
        
        // Destroy cropper lama jika ada
        if (cropper) {
          cropper.destroy();
        }
        
        // Reset scale
        scaleX = 1;
        scaleY = 1;
        
        // Initialize cropper dengan rasio 3:4
        cropper = new Cropper(imageToCrop, {
          aspectRatio: 3 / 4, // Rasio 3:4
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
  rotateLeft.addEventListener('click', function() {
    if (cropper) {
      cropper.rotate(-45);
    }
  });
  
  // Rotate Right
  rotateRight.addEventListener('click', function() {
    if (cropper) {
      cropper.rotate(45);
    }
  });
  
  // Flip Horizontal
  flipHorizontal.addEventListener('click', function() {
    if (cropper) {
      scaleX = scaleX === 1 ? -1 : 1;
      cropper.scaleX(scaleX);
    }
  });
  
  // Flip Vertical
  flipVertical.addEventListener('click', function() {
    if (cropper) {
      scaleY = scaleY === 1 ? -1 : 1;
      cropper.scaleY(scaleY);
    }
  });
  
  // Ketika user klik "Crop & Gunakan"
  cropButton.addEventListener('click', function() {
    if (cropper) {
      // Get cropped canvas dengan ukuran optimal (3:4 ratio)
      const canvas = cropper.getCroppedCanvas({
        width: 600,  // 3:4 ratio (600x800)
        height: 800,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high',
      });
      
      // Convert canvas ke base64 (JPEG dengan quality 0.9)
      const base64Image = canvas.toDataURL('image/jpeg', 0.9);
      
      // Simpan ke hidden input
      avatarData.value = base64Image;
      
      // Update preview
      avatarPreview.src = base64Image;
      previewContainer.style.display = 'block';
      
      // Update current avatar display
      currentAvatar.src = base64Image;
      
      // Close modal
      avatarModal.hide();
      
      // Show success message
      const successMsg = document.createElement('div');
      successMsg.className = 'alert alert-success alert-dismissible fade show mt-3';
      successMsg.innerHTML = `
        <strong>Berhasil!</strong> Foto profil telah di-crop. Klik "Simpan Perubahan" untuk menyimpan.
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      `;
      document.querySelector('.card').insertBefore(successMsg, document.querySelector('form'));
      
      // Auto dismiss after 5 seconds
      setTimeout(() => {
        successMsg.remove();
      }, 5000);
    }
  });
  
  // Clean up when modal is closed
  document.getElementById('avatarModal').addEventListener('hidden.bs.modal', function() {
    if (cropper) {
      cropper.destroy();
      cropper = null;
    }
    // Reset input jika user cancel
    if (!avatarData.value) {
      avatarInput.value = '';
    }
  });
  
  // Prevent form submission if there's an error
  profileForm.addEventListener('submit', function(e) {
    // Optional: Add validation here
    console.log('Form submitted with avatar data:', avatarData.value ? 'Yes' : 'No');
  });
});