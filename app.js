/**
 * POOJA ROOM: GLOBAL APPLICATION SCRIPT
 * Handles Supabase initialization and global state.
 */

// Initialize Supabase Client
const { createClient } = supabase;
const supabaseClient = createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

// Make available globally
window.supabase = supabaseClient;

document.addEventListener('DOMContentLoaded', async () => {
    console.log("Pooja Room: Initializing...");

    // Initial Navbar Render (Placeholder or cached session)
    const { data: { session } } = await window.supabase.auth.getSession();
    window.renderNavbar(session?.user || null);

    // Auth Change Listener
    window.supabase.auth.onAuthStateChange((event, session) => {
        console.log("Auth State Changed:", event);
        window.renderNavbar(session?.user || null);

        // Global redirects for specific events if needed
        if (event === 'SIGNED_OUT') {
            window.location.href = 'index.html';
        }
    });
});
