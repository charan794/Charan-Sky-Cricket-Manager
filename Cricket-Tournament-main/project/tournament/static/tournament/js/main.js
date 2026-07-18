// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function () {
  const navToggle = document.getElementById('navToggle');
  const navMenu = document.getElementById('navMenu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', function () {
      navToggle.classList.toggle('active');
      navMenu.classList.toggle('active');
    });

    // Close menu when a link is clicked (mobile)
    navMenu.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', function () {
        navToggle.classList.remove('active');
        navMenu.classList.remove('active');
      });
    });
  }

  // Auto-dismiss messages after 5 seconds
  document.querySelectorAll('.message').forEach(function (msg) {
    setTimeout(function () {
      msg.style.transition = 'opacity 0.5s ease';
      msg.style.opacity = '0';
      setTimeout(function () { msg.remove(); }, 500);
    }, 5000);
  });
});

// Custom Delete Modal control functions
function confirmDelete(url, itemName, itemType) {
  const modal = document.getElementById('deleteModal');
  const form = document.getElementById('deleteModalForm');
  const message = document.getElementById('deleteModalMessage');

  if (modal && form && message) {
    form.action = url;
    message.textContent = 'Are you sure you want to delete the ' + itemType + ' "' + itemName + '"? This action cannot be undone.';
    modal.classList.add('active');
  }
}

function closeDeleteModal() {
  const modal = document.getElementById('deleteModal');
  if (modal) {
    modal.classList.remove('active');
  }
}

