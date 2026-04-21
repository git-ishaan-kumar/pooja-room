/**
 * POOJA ROOM: MAIN APPLICATION LOGIC
 * Phase 1: Initialization
 */

import { supabase } from './config.js';

// Make supabase available globally for debugging and other scripts if needed
window.supabase = supabase;

/**
 * Renders the navbar based on authentication state
 */
function renderNavbar(user) {
    const navbarContainer = document.getElementById('navbar-container');
    if (!navbarContainer) return;

    const initial = user?.user_metadata?.display_name ? user.user_metadata.display_name[0].toUpperCase() : (user?.email ? user.email[0].toUpperCase() : '?');

    navbarContainer.innerHTML = `
        <nav class="navbar">
            <div class="nav-left">
                <a href="/" class="nav-brand" data-link>
                    <img src="static/assets/icons/icon.svg" alt="Pooja Room" class="nav-logo">
                    <span>Pooja Room</span>
                </a>
                ${user ? `
                    <div class="nav-links">
                        <a href="/" class="nav-link active" data-link>Dashboard</a>
                        <a href="/library" class="nav-link" data-link>Prayers</a>
                    </div>
                ` : ''}
            </div>

            <div class="nav-right">
                ${user ? `
                    <div class="user-profile">
                        ${initial}
                        <div class="dropdown-menu">
                            <a href="/settings" class="dropdown-item" data-link>Account Settings</a>
                            <button id="logout-btn" class="dropdown-item logout">Logout</button>
                        </div>
                    </div>
                ` : `
                    <a href="/signin" class="btn-ghost" data-link>Sign In</a>
                    <a href="/register" class="btn-primary" data-link>Register</a>
                `}
            </div>
        </nav>
    `;

    // Add dropdown and logout listeners if logged in
    if (user) {
        const userProfile = document.querySelector('.user-profile');
        userProfile?.addEventListener('click', (e) => {
            e.stopPropagation();
            userProfile.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            userProfile?.classList.remove('active');
        });

        document.getElementById('logout-btn')?.addEventListener('click', async (e) => {
            e.stopPropagation();
            const { error } = await supabase.auth.signOut();
            if (error) console.error('Error signing out:', error.message);
            navigateTo('/');
        });
    }
}

/**
 * Renders the Registration Page
 */
function renderRegister() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="auth-container">
            <div class="auth-card">
                <h1 class="auth-title">Create an Account</h1>
                <p class="auth-subtitle">Join the technical-minimalist prayer library.</p>
                
                <div id="success-banner" class="success-banner">
                    <strong>Registration Successful!</strong>
                    A verification link has been sent to your email. Please confirm your email to activate your account.
                </div>

                <form id="register-form">
                    <div class="form-group">
                        <label class="form-label" for="display-name">Display Name</label>
                        <input type="text" id="display-name" class="form-input" placeholder="Your name" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="email">Email Address</label>
                        <input type="email" id="email" class="form-input" placeholder="you@example.com" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="password">Password</label>
                        <div class="password-wrapper">
                            <input type="password" id="password" class="form-input" placeholder="••••••••" required>
                            <span class="toggle-password" data-target="password">
                                <svg class="eye-off" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                                <svg class="eye" style="display:none;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                            </span>
                        </div>
                        <div id="password-error" class="error-message">Password must be at least 6 characters.</div>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="confirm-password">Confirm Password</label>
                        <div class="password-wrapper">
                            <input type="password" id="confirm-password" class="form-input" placeholder="••••••••" required>
                            <span class="toggle-password" data-target="confirm-password">
                                <svg class="eye-off" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                                <svg class="eye" style="display:none;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                            </span>
                        </div>
                        <div id="confirm-password-error" class="error-message">Passwords do not match.</div>
                    </div>
                    
                    <div id="general-error" class="error-message"></div>
                    
                    <button type="submit" class="auth-btn">Register</button>
                </form>
                
                <div class="auth-footer">
                    Already have an account? <a href="/signin" class="auth-link" data-link>Sign In</a>
                </div>
            </div>
        </div>
    `;

    document.getElementById('register-form').addEventListener('submit', handleRegister);
    
    // Toggle Password Visibility
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const eyeOff = btn.querySelector('.eye-off');
            const eye = btn.querySelector('.eye');
            
            if (input.type === 'password') {
                input.type = 'text';
                eyeOff.style.display = 'none';
                eye.style.display = 'block';
            } else {
                input.type = 'password';
                eyeOff.style.display = 'block';
                eye.style.display = 'none';
            }
        });
    });
}

/**
 * Handles the registration logic
 */
async function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('display-name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    const passwordError = document.getElementById('password-error');
    const confirmPasswordError = document.getElementById('confirm-password-error');
    const generalError = document.getElementById('general-error');
    
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');

    // Reset errors
    passwordError.style.display = 'none';
    confirmPasswordError.style.display = 'none';
    generalError.style.display = 'none';
    passwordInput.classList.remove('error');
    confirmPasswordInput.classList.remove('error');

    let hasError = false;

    if (password.length < 6) {
        passwordError.style.display = 'block';
        passwordInput.classList.add('error');
        hasError = true;
    }

    if (password !== confirmPassword) {
        confirmPasswordError.style.display = 'block';
        confirmPasswordInput.classList.add('error');
        hasError = true;
    }

    if (hasError) return;

    const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
            data: {
                display_name: name
            }
        }
    });

    if (error) {
        generalError.textContent = error.message;
        generalError.style.display = 'block';
    } else {
        console.log("Registration successful:", data);
        // Show success banner and hide form
        document.getElementById('success-banner').style.display = 'block';
        document.getElementById('register-form').style.display = 'none';
        document.querySelector('.auth-subtitle').style.display = 'none';
        document.querySelector('.auth-title').textContent = 'Check your email';
    }
}

/**
 * Renders the Sign In Page
 */
function renderSignIn() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="auth-container">
            <div class="auth-card">
                <h1 class="auth-title">Welcome back</h1>
                <p class="auth-subtitle">Sign in to your pooja room.</p>
                
                <form id="signin-form">
                    <div class="form-group">
                        <label class="form-label" for="email">Email Address</label>
                        <input type="email" id="email" class="form-input" placeholder="you@example.com" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" for="password">Password</label>
                        <div class="password-wrapper">
                            <input type="password" id="password" class="form-input" placeholder="••••••••" required>
                            <span class="toggle-password" data-target="password">
                                <svg class="eye-off" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                                <svg class="eye" style="display:none;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                            </span>
                        </div>
                    </div>
                    
                    <div id="general-error" class="error-message"></div>
                    
                    <button type="submit" class="auth-btn">Sign In</button>
                </form>
                
                <div class="auth-footer">
                    Don't have an account? <a href="/register" class="auth-link" data-link>Register</a>
                </div>
            </div>
        </div>
    `;

    document.getElementById('signin-form').addEventListener('submit', handleSignIn);

    // Toggle Password Visibility
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const eyeOff = btn.querySelector('.eye-off');
            const eye = btn.querySelector('.eye');
            
            if (input.type === 'password') {
                input.type = 'text';
                eyeOff.style.display = 'none';
                eye.style.display = 'block';
            } else {
                input.type = 'password';
                eyeOff.style.display = 'block';
                eye.style.display = 'none';
            }
        });
    });
}

/**
 * Handles the sign-in logic
 */
async function handleSignIn(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const generalError = document.getElementById('general-error');
    const inputs = document.querySelectorAll('.form-input');

    // Reset errors
    generalError.style.display = 'none';
    inputs.forEach(input => input.classList.remove('error'));

    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
    });

    if (error) {
        generalError.textContent = error.message;
        generalError.style.display = 'block';
        inputs.forEach(input => input.classList.add('error'));
    } else {
        console.log("Sign in successful:", data);
        navigateTo('/');
    }
}

/**
 * Simple Router
 */
function router() {
    const path = window.location.pathname;
    
    if (path === '/register') {
        renderRegister();
    } else if (path === '/signin') {
        renderSignIn();
    } else {
        // Default to landing page or dashboard
        document.getElementById('app').innerHTML = '<div class="auth-container"><h1>Landing / Dashboard (Coming Soon)</h1></div>';
    }
}

/**
 * Navigation Helper
 */
function navigateTo(url) {
    history.pushState(null, null, url);
    router();
}

async function initApp() {
    console.log("Pooja Room initialized.");
    
    // Initial session check
    const { data: { session } } = await supabase.auth.getSession();
    renderNavbar(session?.user || null);

    // Auth state listener
    supabase.auth.onAuthStateChange((event, session) => {
        renderNavbar(session?.user || null);
        if (event === 'SIGNED_IN') {
            navigateTo('/');
        }
    });

    // Handle back/forward buttons
    window.addEventListener('popstate', router);

    // Intercept link clicks for client-side routing
    document.addEventListener('click', e => {
        if (e.target.matches('[data-link]') || e.target.closest('[data-link]')) {
            e.preventDefault();
            const link = e.target.matches('[data-link]') ? e.target : e.target.closest('[data-link]');
            navigateTo(link.getAttribute('href'));
        }
    });

    router();
}

// Start the app
document.addEventListener('DOMContentLoaded', initApp);
