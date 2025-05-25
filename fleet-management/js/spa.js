// js/spa.js
import { API_BASE_URL, checkAuth, handleLogout, updateUserInfoDisplay } from './auth.js';
import { showLoadingSpinner, hideLoadingSpinner } from './utils.js';
import { initializeTableModule, clearTableEventListeners } from './table-manager.js';
import * as modalManager from './modal-manager.js';
// Import specific initializers/cleaners for non-table modules
import { initializeDashboardOverviewModule, cleanupDashboardOverviewModule, handleDashboardOverviewThemeChange } from './dashboard-overview.js';


// --- Authentication Guard ---
if (window.location.pathname.includes('dashboard.html')) {
    if (!checkAuth(true)) {
        console.error("User not authenticated. Halting spa.js execution.");
        throw new Error("User not authenticated. Redirecting to login.");
    }
}

// DOM Elements
const mainContentArea = document.getElementById('main-content-area');
const initialLoader = document.getElementById('initial-loader');
const navList = document.getElementById('main-nav-list');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebar-overlay');
const mobileMenuButton = document.getElementById('mobile-menu-button');
const closeSidebarButton = document.getElementById('close-sidebar-button');
const themeToggleButton = document.getElementById('theme-toggle');

// Global SPA State
export let currentModuleConfig = {};

// Module specific handlers
const moduleInitFunctions = {
    'dashboard_overview': initializeDashboardOverviewModule,
    // For generic table modules, initializeTableModule will be called if no specific init is found
};
const moduleCleanupFunctions = {
    'dashboard_overview': cleanupDashboardOverviewModule,
    // For generic table modules, clearTableEventListeners is the default cleanup
};
const moduleThemeChangeHandlers = {
    'dashboard_overview': handleDashboardOverviewThemeChange,
};

// --- Mobile Menu Logic ---
function openMobileSidebar() {
    if (sidebar) sidebar.classList.remove('-translate-x-full');
    if (sidebar) sidebar.classList.add('translate-x-0');
    if (sidebarOverlay) sidebarOverlay.classList.remove('hidden');
    document.body.classList.add('overflow-hidden', 'md:overflow-auto');
}

function closeMobileSidebar() {
    if (sidebar) sidebar.classList.add('-translate-x-full');
    if (sidebar) sidebar.classList.remove('translate-x-0');
    if (sidebarOverlay) sidebarOverlay.classList.add('hidden');
    document.body.classList.remove('overflow-hidden', 'md:overflow-auto');
}

// --- Theme Toggle Logic ---
function applyTheme(theme) {
    const oldTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    const iconName = theme === 'dark' ? 'sun' : 'moon';
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    if (themeToggleButton) {
        themeToggleButton.innerHTML = `<i data-lucide="${iconName}" class="w-5 h-5"></i>`;
        lucide.createIcons({ nodes: [themeToggleButton] });
    }

    if (oldTheme !== theme && currentModuleConfig.name && typeof moduleThemeChangeHandlers[currentModuleConfig.name] === 'function') {
        moduleThemeChangeHandlers[currentModuleConfig.name]();
    }
}

// --- API Request Function (Centralized) ---
export async function apiRequest(endpoint, method = 'GET', body = null, isFormData = false) {
    const token = localStorage.getItem('accessToken');
    const headers = {};

    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    } else {
        console.warn(`API request to ${endpoint} made without an access token.`);
    }

    const config = { method, headers };
    if (body) {
        config.body = isFormData ? body : JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        if (response.status === 401) {
            console.warn(`API request to ${endpoint} resulted in 401. Logging out.`);
            handleLogout();
            return null;
        }
        if (response.status === 204) return true;

        let responseData;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            responseData = await response.json();
        } else {
            const textResponse = await response.text();
            if (!response.ok) {
                console.error(`API Error (Non-JSON) for ${endpoint}: ${response.status}`, textResponse);
                modalManager.openInfoStatusModal(`API Error: ${response.status}`, `Server responded with: ${textResponse.substring(0, 100)}...`, "error");
                return null;
            }
            return textResponse;
        }

        if (!response.ok) {
            const errorDetail = responseData.detail || JSON.stringify(responseData) || 'Unknown server error.';
            console.error(`API Error (JSON) for ${endpoint}: ${response.status}`, errorDetail);
            modalManager.openInfoStatusModal(`API Error: ${response.status}`, errorDetail, "error");
            return null;
        }
        return responseData;
    } catch (error) {
        console.error(`Network/Catch Error during API request to ${endpoint}:`, error);
        const errorMessage = error.detail || error.message || "A network or request error occurred.";
        modalManager.openInfoStatusModal("Request Error", errorMessage, "error");
        return null;
    }
}

// --- Content Loading Logic ---
async function loadContent(navLinkElement) {
    if (!navLinkElement || !navLinkElement.dataset.contentUrl) {
        console.warn("No valid nav link element or content URL provided to loadContent.");
        if (mainContentArea) mainContentArea.innerHTML = `<p class="p-4 text-center text-red-500">Module not found or configuration error.</p>`;
        if (initialLoader) initialLoader.classList.add('hidden');
        return;
    }

    // Cleanup previous module
    if (currentModuleConfig.name && typeof moduleCleanupFunctions[currentModuleConfig.name] === 'function') {
        console.log(`Cleaning up module: ${currentModuleConfig.name}`);
        moduleCleanupFunctions[currentModuleConfig.name]();
    }
    clearTableEventListeners(); // Always run generic table cleanup
    modalManager.closeAllModals();

    const contentUrl = navLinkElement.dataset.contentUrl;
    const moduleName = navLinkElement.dataset.module;
    const targetHref = navLinkElement.getAttribute('href');

    // Update currentModuleConfig with data from the clicked link
    currentModuleConfig = {
        name: moduleName,
        title: navLinkElement.dataset.title || 'Page',
        contentUrl: contentUrl, // Storing for reference, though not directly used after fetching
        apiEndpoint: navLinkElement.dataset.apiEndpoint,
        columns: navLinkElement.dataset.columns ? JSON.parse(navLinkElement.dataset.columns) : [],
        formFields: navLinkElement.dataset.formFields ? JSON.parse(navLinkElement.dataset.formFields) : [],
        viewFields: navLinkElement.dataset.viewFields ? JSON.parse(navLinkElement.dataset.viewFields) : [],
        hasDateFilters: navLinkElement.dataset.dateFilters === 'true',
        statusFilterKey: navLinkElement.dataset.statusFilterKey,
        statusFilterOptions: navLinkElement.dataset.statusFilterOptions ? JSON.parse(navLinkElement.dataset.statusFilterOptions) : [],
    };

    if (initialLoader) initialLoader.classList.add('hidden');
    showLoadingSpinner('main-content-area');
    if (mainContentArea) mainContentArea.innerHTML = '';

    try {
        const response = await fetch(contentUrl); // Fetch the HTML template
        if (!response.ok) throw new Error(`Failed to load content template: ${response.status} from ${contentUrl}`);
        const html = await response.text();
        if (mainContentArea) mainContentArea.innerHTML = html;

        lucide.createIcons({ nodes: [mainContentArea], attrs: {'stroke-width': 1.8 } });

        history.pushState({ module: moduleName, href: targetHref }, '', targetHref);
        updateActiveNavLink(targetHref);
        document.title = `FleetDash - ${currentModuleConfig.title || moduleName}`;

        // Initialize the loaded module
        if (typeof moduleInitFunctions[currentModuleConfig.name] === 'function') {
            console.log(`Initializing specific module: ${currentModuleConfig.name}`);
            await moduleInitFunctions[currentModuleConfig.name](currentModuleConfig); // Pass full config
        } else if (currentModuleConfig.apiEndpoint && contentUrl.includes('table-template.html')) {
            console.log(`Initializing generic table module: ${currentModuleConfig.name}`);
            await initializeTableModule(currentModuleConfig); // Pass full config
        } else {
            console.log(`Module ${currentModuleConfig.name} loaded, no specific initializer or table config found.`);
        }

    } catch (error) {
        console.error("Error loading or initializing content:", error);
        if (mainContentArea) {
            mainContentArea.innerHTML = `<div class="p-6 text-center">
                <i data-lucide="alert-circle" class="w-12 h-12 mx-auto text-red-500 mb-4"></i>
                <h3 class="text-xl font-semibold text-red-600 dark:text-red-400">Content Load Error</h3>
                <p class="text-gray-600 dark:text-gray-400 mt-2">${error.message}.</p>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">Attempted to load: ${contentUrl}</p>
            </div>`;
            lucide.createIcons({ nodes: [mainContentArea] });
        }
    } finally {
        hideLoadingSpinner('main-content-area');
    }
}

// --- UI Update Functions ---
function updateActiveNavLink(activeHref) {
    if (!navList) return;
    const navLinks = navList.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const listItem = link.closest('.nav-item');
        if (!listItem) return;

        const isActive = link.getAttribute('href') === activeHref;
        listItem.classList.toggle('active-link', isActive); // Keep a general active class
        listItem.classList.toggle('bg-blue-50', isActive);
        listItem.classList.toggle('dark:bg-gray-700', isActive);
        link.classList.toggle('text-primary', isActive);
        link.classList.toggle('dark:text-primary-light', isActive);
        link.classList.toggle('font-semibold', isActive);
        link.querySelector('i')?.classList.toggle('text-primary', isActive);
        link.querySelector('i')?.classList.toggle('dark:text-primary-light', isActive);
    });
}

// --- DOMContentLoaded ---
document.addEventListener('DOMContentLoaded', async () => {
    lucide.createIcons();
    await updateUserInfoDisplay();
    modalManager.initializeModalEventListeners();

    const savedTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    applyTheme(savedTheme);
    if (themeToggleButton) {
        themeToggleButton.addEventListener('click', () => {
            const isDark = document.documentElement.classList.contains('dark');
            const newTheme = isDark ? 'light' : 'dark';
            localStorage.setItem('theme', newTheme);
            applyTheme(newTheme);
        });
    }

    if (mobileMenuButton) mobileMenuButton.addEventListener('click', openMobileSidebar);
    if (closeSidebarButton) closeSidebarButton.addEventListener('click', closeMobileSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeMobileSidebar);

    if (navList) {
        navList.addEventListener('click', (event) => {
            const navLink = event.target.closest('.nav-link');
            if (navLink && navLink.dataset.contentUrl) {
                event.preventDefault();
                loadContent(navLink);
                if (window.innerWidth < 768 && sidebar && sidebar.classList.contains('translate-x-0')) {
                    closeMobileSidebar();
                }
            }
        });
    }

    window.addEventListener('popstate', (event) => {
        const targetHref = (event.state && event.state.href) ? event.state.href : (window.location.hash || '#dashboard_overview');
        const linkToLoad = navList ? navList.querySelector(`.nav-link[href="${targetHref}"]`) : null;
        if (linkToLoad) {
            loadContent(linkToLoad);
        } else {
            console.warn(`No link found for popstate href: ${targetHref}. Loading default.`);
            const defaultLink = navList ? (navList.querySelector('.nav-link[data-module="dashboard_overview"]') || navList.querySelector('.nav-link')) : null;
            if (defaultLink) loadContent(defaultLink);
        }
    });

    const initialHash = window.location.hash || '#dashboard_overview';
    const initialNavLink = navList ? (navList.querySelector(`.nav-link[href="${initialHash}"]`) || navList.querySelector('.nav-link[data-module="dashboard_overview"]')) : null;

    if (initialNavLink) {
        await loadContent(initialNavLink);
    } else {
        if (mainContentArea) mainContentArea.innerHTML = "<p class='p-4 text-center'>Welcome! Please select a module from the menu.</p>";
        if (initialLoader) initialLoader.classList.add('hidden');
    }

    document.getElementById('global-logout-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        handleLogout();
    });
});

// Expose modalManager to window if dashboard-overview.js or other modules need to call it via window
// This is a simpler way than event emitters for now.
window.modalManager = modalManager;
    
