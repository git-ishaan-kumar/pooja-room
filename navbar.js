/**
 * POOJA ROOM: NAVBAR COMPONENT
 * Handles dynamic rendering of the navigation bar based on auth state.
 */

function renderNavbar(user) {
    const navbarContainer = document.getElementById('navbar-container');
    if (!navbarContainer) return;

    const initial = user?.user_metadata?.display_name 
        ? user.user_metadata.display_name.charAt(0).toUpperCase() 
        : (user?.email ? user.email.charAt(0).toUpperCase() : '?');

    // Logo destination based on auth state
    const logoHref = user ? 'dashboard.html' : 'index.html';

    navbarContainer.innerHTML = `
        <div class="nav-content container">
            <!-- Left: Branding -->
            <div class="nav-left">
                <a href="${logoHref}" class="nav-brand">
                    <img src="static/assets/icons/icon.svg" alt="Pooja Room Logo">
                    <span>Pooja Room</span>
                </a>
                ${user ? `
                <nav class="nav-links">
                    <a href="dashboard.html" class="nav-link ${window.location.pathname.endsWith('dashboard.html') ? 'active' : ''}">Dashboard</a>
                </nav>
                ` : ''}
            </div>

            <!-- Center: Global Search -->
            <div class="nav-search">
                <span class="search-icon">🔍</span>
                <input type="text" placeholder="Search 1,164 prayers..." id="global-search">
            </div>

            <!-- Right: User Actions -->
            <div class="nav-right">
                <div class="nav-actions">
                    ${user ? `
                        <div class="user-profile">
                            <div class="profile-circle">${initial}</div>
                            <div class="dropdown-menu">
                                <a href="settings.html" class="dropdown-item">Account Settings</a>
                                <a href="#" id="logout-btn" class="dropdown-item logout-item">Logout</a>
                            </div>
                        </div>
                    ` : `
                        <a href="login.html" class="btn-ghost">Sign In</a>
                        <a href="register.html" class="btn-primary">Register</a>
                    `}
                </div>
            </div>
        </div>
    `;

    // Attach Logout Logic
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const { error } = await window.supabase.auth.signOut();
            if (error) console.error("Logout Error:", error.message);
            window.location.href = 'index.html';
        });
    }

    // Dropdown Toggle Logic
    const userProfile = document.querySelector('.user-profile');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    if (userProfile && dropdownMenu) {
        userProfile.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            dropdownMenu.classList.remove('show');
        });
    }
}

// Export to window for global access
window.renderNavbar = renderNavbar;
