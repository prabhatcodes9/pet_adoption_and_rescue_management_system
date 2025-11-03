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
    // -----------------------
    // Modal Open/Close Setup
    // -----------------------
    if (loginBtn) loginBtn.addEventListener('click', openLoginModal);
    if (closeLogin) closeLogin.addEventListener('click', closeLoginModal);
    if (closeRegister) closeRegister.addEventListener('click', closeRegisterModal);

    if (switchToRegister) switchToRegister.addEventListener('click', function(e){ e.preventDefault(); switchToRegisterModal(); });
    if (switchToLogin) switchToLogin.addEventListener('click', function(e){ e.preventDefault(); switchToLoginModal(); });

    if (logoutBtn) logoutBtn.addEventListener('click', function(){ window.location.href = "/logout"; });

    // Auto-open modal if URL contains query param
    const params = new URLSearchParams(window.location.search);
    if (params.get('show_login') === '1') openLoginModal();
    if (params.get('show_register') === '1') openRegisterModal();

    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === loginModal) closeLoginModal();
        if (event.target === registerModal) closeRegisterModal();
    });

    // Escape key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (loginModal && loginModal.style.display === 'block') closeLoginModal();
            if (registerModal && registerModal.style.display === 'block') closeRegisterModal();
        }
    });

    // -----------------------
    // OTP Verification Logic
    // -----------------------
    const sendOtpBtn = document.getElementById('sendOtpBtn');
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    const otpSection = document.getElementById('otpSection');
    const otpStatus = document.getElementById('otpStatus');
    const registerForm = document.getElementById('registrationForm');
    let registerBtn = null;
    let otpVerified = false;

    if (registerForm) {
        registerBtn = registerForm.querySelector('button[type="submit"]');
        if (registerBtn) registerBtn.disabled = true; // disable register until OTP verified
    }

    // Send OTP
    if (sendOtpBtn) {
        sendOtpBtn.addEventListener('click', async () => {
            const email = document.querySelector('#registrationForm input[name="email"]').value;
            if (!email) return alert('Please enter your email first.');

            sendOtpBtn.disabled = true;
            sendOtpBtn.textContent = "Sending...";

            try {
                const res = await fetch('/send_otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await res.json();

                if (data.status === 'success') {
                    if (otpSection) otpSection.style.display = 'block';
                    if (otpStatus) {
                        otpStatus.textContent = 'OTP sent to your email.';
                        otpStatus.style.color = 'green';
                    }
                } else {
                    if (otpStatus) {
                        otpStatus.textContent = data.message || 'Error sending OTP.';
                        otpStatus.style.color = 'red';
                    }
                }
            } catch (error) {
                alert('Error sending OTP. Try again later.');
            } finally {
                sendOtpBtn.disabled = false;
                sendOtpBtn.textContent = "Send OTP";
            }
        });
    }

    // Verify OTP
    if (verifyOtpBtn) {
        verifyOtpBtn.addEventListener('click', async () => {
            const email = document.querySelector('#registrationForm input[name="email"]').value;
            const otp = document.getElementById('otp').value;
            if (!otp) return alert('Enter your OTP.');

            verifyOtpBtn.disabled = true;
            verifyOtpBtn.textContent = "Verifying...";

            try {
                const res = await fetch('/verify_otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, otp })
                });
                const data = await res.json();

                if (data.status === 'verified') {
                    otpVerified = true;
                    if (registerBtn) registerBtn.disabled = false;
                    if (otpStatus) {
                        otpStatus.textContent = 'Email verified successfully!';
                        otpStatus.style.color = 'green';
                    }
                } else {
                    otpVerified = false;
                    if (otpStatus) {
                        otpStatus.textContent = data.message || 'Invalid OTP.';
                        otpStatus.style.color = 'red';
                    }
                }
            } catch (error) {
                alert('Error verifying OTP. Try again later.');
            } finally {
                verifyOtpBtn.disabled = false;
                verifyOtpBtn.textContent = "Verify OTP";
            }
        });
    }

    // Prevent registration if OTP not verified
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            if (!otpVerified) {
                e.preventDefault();
                alert('Please verify your email OTP before registering.');
            }
        });
    }
});

// -----------------------
// Modal Control Functions
// -----------------------
function openLoginModal(){ if (loginModal) loginModal.style.display = 'block'; }
function closeLoginModal(){ if (loginModal){ loginModal.style.display = 'none'; const f = document.getElementById('loginForm'); if(f) f.reset(); } }
function openRegisterModal(){ if (registerModal) registerModal.style.display = 'block'; }
function closeRegisterModal(){ if (registerModal){ registerModal.style.display = 'none'; const f = document.getElementById('registrationForm'); if(f) f.reset(); } }
function switchToRegisterModal(){ closeLoginModal(); openRegisterModal(); }
function switchToLoginModal(){ closeRegisterModal(); openLoginModal(); }

// -----------------------
// Card Action Handlers
// -----------------------
function handleActionClick(action) {
    if (action === 'lost') { window.location.href = '/report_lost'; }
    else if (action === 'found') { window.location.href = '/report_found'; }
    else if (action === 'adopt') { window.location.href = '/report_adopt'; }
}