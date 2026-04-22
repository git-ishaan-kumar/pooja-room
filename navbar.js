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
    const logoHref = user ? '/dashboard' : '/';

    navbarContainer.innerHTML = `
        <div class="nav-content container">
            <!-- Left: Branding -->
            <div class="nav-left">
                <a href="${logoHref}" class="nav-brand">
                    <img src="static/assets/icons/icon.svg" alt="Pooja Room Logo">
                    <span>Pooja Room</span>
                </a>
                ${user ? `
                <nav class="nav-links desktop-only">
                    <a href="/dashboard" class="nav-link ${window.location.pathname.endsWith('/dashboard') ? 'active' : ''}">Dashboard</a>
                    <a href="/library" class="nav-link ${window.location.pathname.endsWith('/library') ? 'active' : ''}">Prayers</a>
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
                                <a href="/settings" class="dropdown-item">Account Settings</a>
                                <a href="#" id="logout-btn" class="dropdown-item logout-item">Logout</a>
                            </div>
                        </div>
                    ` : `
                        <a href="/login" class="btn-ghost desktop-only">Sign In</a>
                        <a href="/register" class="btn-primary desktop-only">Register</a>
                    `}
                    <button id="nav-toggle" class="nav-toggle" aria-label="Toggle Navigation">
                        <span class="hamburger-line"></span>
                        <span class="hamburger-line"></span>
                        <span class="hamburger-line"></span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Mobile Menu -->
        <div id="mobile-menu" class="mobile-menu">
            ${user ? `
                <div class="mobile-nav-links">
                    <a href="/dashboard" class="mobile-nav-link ${window.location.pathname.endsWith('/dashboard') ? 'active' : ''}">Dashboard</a>
                    <a href="/library" class="mobile-nav-link ${window.location.pathname.endsWith('/library') ? 'active' : ''}">Prayers</a>
                    <a href="/settings" class="mobile-nav-link ${window.location.pathname.endsWith('/settings') ? 'active' : ''}">Account Settings</a>
                    <a href="#" id="mobile-logout-btn" class="mobile-nav-link logout-item">Logout</a>
                </div>
            ` : `
                <div class="mobile-nav-links">
                    <a href="/" class="mobile-nav-link">Home</a>
                    <a href="/login" class="mobile-nav-link">Sign In</a>
                    <a href="/register" class="mobile-nav-link">Register</a>
                </div>
            `}
        </div>
    `;

    // Attach Logout Logic (Desktop & Mobile)
    const attachLogout = (id) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const { error } = await window.supabase.auth.signOut();
                if (error) console.error("Logout Error:", error.message);
                window.location.href = '/';
            });
        }
    };
    attachLogout('logout-btn');
    attachLogout('mobile-logout-btn');

    // Mobile Menu Toggle Logic
    const navToggle = document.getElementById('nav-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    if (navToggle && mobileMenu) {
        navToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            navToggle.classList.toggle('active');
            mobileMenu.classList.toggle('active');
            document.body.classList.toggle('no-scroll');
        });

        // Close menu when clicking links
        const mobileLinks = mobileMenu.querySelectorAll('.mobile-nav-link');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                navToggle.classList.remove('active');
                mobileMenu.classList.remove('active');
                document.body.classList.remove('no-scroll');
            });
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenu.contains(e.target) && !navToggle.contains(e.target)) {
                navToggle.classList.remove('active');
                mobileMenu.classList.remove('active');
                document.body.classList.remove('no-scroll');
            }
        });
    }

    // Dropdown Toggle Logic (Desktop Only)
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

    // Global Search Redirect Logic
    const globalSearch = document.getElementById('global-search');
    if (globalSearch) {
        globalSearch.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && globalSearch.value.trim().length > 0) {
                window.location.href = `/library?q=${encodeURIComponent(globalSearch.value.trim())}`;
            }
        });
    }
}

// Export to window for global access
window.renderNavbar = renderNavbar;
