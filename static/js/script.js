// static/js/script.js

const loginBtn = document.getElementById('loginBtn');
const loginModal = document.getElementById('loginModal');
const registerModal = document.getElementById('registerModal');
const closeLogin = document.getElementById('closeLogin');
const closeRegister = document.getElementById('closeRegister');
const switchToRegister = document.getElementById('switchToRegister');
const switchToLogin = document.getElementById('switchToLogin');
const logoutBtn = document.getElementById('logoutBtn');

document.addEventListener('DOMContentLoaded', function() {
    if (loginBtn) loginBtn.addEventListener('click', openLoginModal);
    if (closeLogin) closeLogin.addEventListener('click', closeLoginModal);
    if (closeRegister) closeRegister.addEventListener('click', closeRegisterModal);

    if (switchToRegister) switchToRegister.addEventListener('click', function(e){ e.preventDefault(); switchToRegisterModal(); });
    if (switchToLogin) switchToLogin.addEventListener('click', function(e){ e.preventDefault(); switchToLoginModal(); });

    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(){ window.location.href = "/logout"; });
    }

    // Auto-open modal if URL contains query param
    const params = new URLSearchParams(window.location.search);
    if (params.get('show_login') === '1') openLoginModal();
    if (params.get('show_register') === '1') openRegisterModal();

    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === loginModal) closeLoginModal();
        if (event.target === registerModal) closeRegisterModal();
    });

    // Escape to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (loginModal && loginModal.style.display === 'block') closeLoginModal();
            if (registerModal && registerModal.style.display === 'block') closeRegisterModal();
        }
    });
});

function openLoginModal(){ if (loginModal) loginModal.style.display = 'block'; }
function closeLoginModal(){ if (loginModal){ loginModal.style.display = 'none'; const f = document.getElementById('loginForm'); if(f) f.reset(); } }
function openRegisterModal(){ if (registerModal) registerModal.style.display = 'block'; }
function closeRegisterModal(){ if (registerModal){ registerModal.style.display = 'none'; const f = document.getElementById('registrationForm'); if(f) f.reset(); } }
function switchToRegisterModal(){ closeLoginModal(); openRegisterModal(); }
function switchToLoginModal(){ closeRegisterModal(); openLoginModal(); }

// Action card handlers (navigate to endpoints)
function handleActionClick(action) {
    if (action === 'lost') { window.location.href = '/report_lost'; }
    else if (action === 'found') { window.location.href = '/report_found'; }
    else if (action === 'adopt') { alert('Adoption listing not implemented yet'); }
}