// static/js/global.js

// --- Simple Toast Notification System ---
function showToast(message, duration = 3000, type = 'info') { // type can be 'info', 'success', 'error'
    const container = document.getElementById('toast-container');
    // Create container if it doesn't exist (useful if not all pages have it hardcoded)
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'toast-container';
        // Basic styling for the container if created dynamically
        newContainer.style.position = 'fixed';
        newContainer.style.bottom = '20px';
        newContainer.style.right = '20px';
        newContainer.style.zIndex = '10000';
        newContainer.style.display = 'flex';
        newContainer.style.flexDirection = 'column';
        newContainer.style.gap = '0.5rem';
        document.body.appendChild(newContainer);
        container = newContainer;
    }

    const toastElement = document.createElement('div');
    toastElement.textContent = message;
    // Basic styling for the toast message itself
    toastElement.style.backgroundColor = '#333';
    toastElement.style.color = 'white';
    toastElement.style.padding = '10px 15px';
    toastElement.style.borderRadius = '5px';
    toastElement.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    toastElement.style.fontSize = '0.875rem';
    toastElement.style.opacity = '1';
    toastElement.style.transition = 'opacity 0.3s ease-out';

    if (type === 'success') {
        toastElement.style.backgroundColor = '#10b981'; // Tailwind green-500
    } else if (type === 'error') {
        toastElement.style.backgroundColor = '#ef4444'; // Tailwind red-500
    } else if (type === 'info') {
        toastElement.style.backgroundColor = '#3b82f6'; // Tailwind blue-500
    }
    
    container.appendChild(toastElement);
    setTimeout(() => {
        toastElement.style.opacity = '0';
        setTimeout(() => {
          toastElement.remove();
        }, 300); // Allow time for fade out
    }, duration);
}


document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Lucide Icons ---
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    } else {
        console.warn("Lucide library not found. Icons will not be rendered.");
    }

    // --- Sidebar Toggle Functionality ---
    const sidebar = document.getElementById('sidebar');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const sidebarCloseButton = document.getElementById('sidebar-close-button'); 
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function openMobileMenu() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.remove('-translate-x-full');
            sidebar.classList.add('translate-x-0');
            sidebarOverlay.classList.remove('hidden');
            document.body.classList.add('overflow-hidden', 'md:overflow-auto'); // Prevent body scroll on mobile
        }
    }

    function closeMobileMenu() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('translate-x-0');
            sidebarOverlay.classList.add('hidden');
            document.body.classList.remove('overflow-hidden'); // Re-enable body scroll
        }
    }

    mobileMenuButton?.addEventListener('click', openMobileMenu);
    sidebarCloseButton?.addEventListener('click', closeMobileMenu);
    sidebarOverlay?.addEventListener('click', closeMobileMenu);

    // Close mobile sidebar when a nav link is clicked (optional, good UX)
    document.querySelectorAll('#sidebar nav a').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 768) { // Only for mobile view
                closeMobileMenu();
            }
        });
    });
    
    // Adjust body overflow if resizing from mobile with open menu to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            document.body.classList.remove('overflow-hidden');
            if (sidebarOverlay && !sidebarOverlay.classList.contains('hidden')) {
                sidebarOverlay.classList.add('hidden'); // Ensure overlay is hidden on desktop
            }
        } else {
            // If sidebar is open on mobile, ensure body overflow is hidden
            if (sidebar && sidebar.classList.contains('translate-x-0') && !sidebar.classList.contains('-translate-x-full')) {
                if (!document.body.classList.contains('overflow-hidden')) {
                     document.body.classList.add('overflow-hidden', 'md:overflow-auto');
                }
            }
        }
    });


    // --- Theme Toggle ---
    // Assumes button has id 'theme-toggle-header' and uses lucide icons 'sun'/'moon'
    const themeToggleButtonHeader = document.getElementById('theme-toggle-header'); 
    
    function updateThemeIcon() {
        if (themeToggleButtonHeader) { 
            if (document.documentElement.classList.contains('dark')) {
                themeToggleButtonHeader.innerHTML = '<i data-lucide="sun" class="w-5 h-5"></i>';
            } else {
                themeToggleButtonHeader.innerHTML = '<i data-lucide="moon" class="w-5 h-5"></i>';
            }
            if (typeof lucide !== 'undefined') lucide.createIcons(); // Re-render the new icon
        }
    }

    // Set initial theme based on localStorage or system preference
    if (localStorage.getItem('theme') === 'dark' || 
        (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    updateThemeIcon(); // Set initial icon

    themeToggleButtonHeader?.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        if (document.documentElement.classList.contains('dark')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
        updateThemeIcon();
        // If you have charts that need re-rendering on theme change, dispatch a custom event
        // window.dispatchEvent(new CustomEvent('themeChanged')); 
        // And then listen for this event in your chart initialization scripts.
        // For analytics.html, it already re-initializes charts on theme change.
    });


    // --- User Info Display (Example: updates elements if they exist) ---
    // This function might be called by individual pages after they ensure elements are ready
    // or if user info is mostly static after login.
    function updateGlobalUserInfoDisplay() {
        const storedUsername = localStorage.getItem('username');
        
        const userNameHeader = document.getElementById('userDisplayNameHeader');
        const userNameSidebar = document.getElementById('userDisplayNameRightSidebar');

        if (userNameHeader && storedUsername) {
            userNameHeader.textContent = storedUsername;
        } else if (userNameHeader) {
            userNameHeader.textContent = "User"; // Default
        }

        if (userNameSidebar && storedUsername) {
            userNameSidebar.textContent = storedUsername;
        } else if (userNameSidebar) {
             userNameSidebar.textContent = "User"; // Default
        }
        // Add more elements to update if needed (e.g., profile picture src)
    }
    updateGlobalUserInfoDisplay(); // Call it once on load


    // --- Global Logout Button Functionality ---
    const logoutButton = document.getElementById('global-logout-btn');
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => { 
            e.preventDefault(); 
            console.log("Global logout clicked from page:", window.location.pathname); 
            
            localStorage.removeItem('accessToken'); 
            localStorage.removeItem('refreshToken'); // If you use this key
            localStorage.removeItem('username');     
            localStorage.removeItem('user_id');      // If you store this
            localStorage.removeItem('user_status');  // If you store this
            
            showToast("Logged out successfully. Redirecting...", 2000, "success"); 
            
            setTimeout(() => {
                // ** IMPORTANT: Verify this path leads to your login page **
                // Examples: "/", "/login.html", "/static/login.html"
                window.location.href = "/"; // Assuming login.html is at the root
            }, 1500); 
        });
    } else {
        console.warn("Logout button with ID 'global-logout-btn' not found on this page.");
    }

}); // End of DOMContentLoaded