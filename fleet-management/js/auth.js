// js/auth.js
export const API_BASE_URL = 'http://localhost:8000';
export const LOGIN_PAGE_URL = 'login.html'; // Relative path to login.html from dashboard.html

export function getAuthToken() {
    return localStorage.getItem('accessToken');
}

export function getUserInfo() {
    const userInfoString = localStorage.getItem('userInfo');
    try {
        return userInfoString ? JSON.parse(userInfoString) : null;
    } catch (e) {
        console.error("Error parsing userInfo from localStorage", e);
        return null;
    }
}

export function parseJwt(token) {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        // console.error("JWT Parse Error:", e); // Can be noisy
        return null;
    }
}

export function checkAuth(redirectToLogin = true) {
    const token = getAuthToken();
    if (!token) {
        if (redirectToLogin) window.location.href = LOGIN_PAGE_URL;
        return false;
    }

    const decodedToken = parseJwt(token);
    if (decodedToken && decodedToken.exp * 1000 < Date.now()) {
        console.log("Token expired.");
        localStorage.removeItem('accessToken');
        localStorage.removeItem('userInfo'); // Also clear userInfo
        if (redirectToLogin) window.location.href = LOGIN_PAGE_URL;
        return false;
    }
    // Your backend /get_current_user re-validates status, which is good.
    // Here, we're just doing a basic client-side check.
    return true;
}

export async function updateUserInfoDisplay() {
    const userDisplayElement = document.getElementById('userDisplayName');
    const userRoleElement = document.getElementById('userRole'); // Assuming you have an element for role/status

    const storedUserInfo = getUserInfo(); // Get from localStorage first

    if (userDisplayElement && storedUserInfo) {
        userDisplayElement.textContent = storedUserInfo.username || 'User';
        // Assuming 'status' from JWT payload or login response is what you want to show as role/status
        userRoleElement.textContent = storedUserInfo.status ? storedUserInfo.status.charAt(0).toUpperCase() + storedUserInfo.status.slice(1) : 'Active';
    } else if (userDisplayElement) { // Fallback if no stored info but token exists (e.g. direct navigation with valid token)
        const token = getAuthToken();
        if (token) {
            const decoded = parseJwt(token);
            if (decoded) {
                userDisplayElement.textContent = decoded.sub || 'User'; // 'sub' is username
                userRoleElement.textContent = decoded.status ? decoded.status.charAt(0).toUpperCase() + decoded.status.slice(1) : 'Active';
            } else {
                 userDisplayElement.textContent = 'Guest';
                 userRoleElement.textContent = '';
            }
        } else {
            userDisplayElement.textContent = 'Guest';
            userRoleElement.textContent = '';
        }
    }
}


export function handleLogout(showModal = true) { // Added showModal param
    const token = getAuthToken(); // Get token before removing for potential /logout API call

    localStorage.removeItem('accessToken');
    localStorage.removeItem('tokenType');
    localStorage.removeItem('userInfo');

    // Optional: Call a backend /logout endpoint if you have one to invalidate server-side sessions or log the logout
    // if (token) {
    //     fetch(`${API_BASE_URL}/logout`, { method: 'POST', headers: {'Authorization': `Bearer ${token}`} })
    //         .catch(err => console.error("Error calling backend logout:", err));
    // }
    if (showModal && typeof window.modalManager !== 'undefined' && typeof window.modalManager.openInfoStatusModal === 'function') {
         // Use a slight delay for the modal to be visible before redirect
        window.modalManager.openInfoStatusModal('Logged Out', 'You have been successfully logged out.', 'success', 1500);
        setTimeout(() => {
            window.location.href = LOGIN_PAGE_URL;
        }, 1600);
    } else {
        window.location.href = LOGIN_PAGE_URL;
    }
}

// Initial check when auth.js is loaded (if dashboard.html)
if (window.location.pathname.includes('dashboard.html')) {
    if (!checkAuth()) {
        // Redirect is handled by checkAuth.
        // Stop further script execution on dashboard.html if not authenticated.
        // This can be tricky with ES modules. A common pattern is to have a guard
        // at the very top of spa.js or dashboard.html's main script.
    }
}