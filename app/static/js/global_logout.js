// File: app/static/js/global_logout.js

// Configuration object for global settings.
// This makes it easier to manage these values if they need to change.
const GLOBAL_CONFIG = {
    LOGIN_PAGE_URL: "/loginpage",     // The URL of your main login page
    LOGOUT_BUTTON_ID: "global-logout-btn" // The ID you will use for your global logout button/link
};

/**
 * Handles the global logout process:
 * - Removes the access token from localStorage.
 * - Optionally removes other user-specific data from localStorage.
 * - Shows a confirmation/notification (currently an alert).
 * - Redirects the user to the login page.
 */
function handleGlobalLogout() {
    console.log("Executing global logout sequence...");

    // Primary action: Remove the access token
    localStorage.removeItem('access_token');

    // Optional: Remove any other user-specific or session-like data stored in localStorage
    // Example:
    // localStorage.removeItem('user_id');
    // localStorage.removeItem('username');
    // localStorage.removeItem('user_preferences');
    // localStorage.removeItem('last_visited_page');

    // Provide feedback to the user.
    // For a real application, you might replace this with a less intrusive
    // toast notification or a brief message within the UI before redirecting.
    alert("You have been logged out. You will now be redirected to the login page.");

    // Redirect to the configured login page URL
    window.location.href = GLOBAL_CONFIG.LOGIN_PAGE_URL;
}

/* // This function will run once the HTML document's initial structure is fully loaded and parsed.
document.addEventListener('DOMContentLoaded', () => {
    // Attempt to find the global logout button using the configured ID.
    const logoutButton = document.getElementById(GLOBAL_CONFIG.LOGOUT_BUTTON_ID);

    if (logoutButton) {
        // If the button is found, attach a click event listener to it.
        logoutButton.addEventListener('click', function(event) {
            // Prevent the default action of the element (e.g., if it's an <a> tag, prevent navigation).
            event.preventDefault();

            // Call the main logout handling function.
            handleGlobalLogout();
        });
        console.log(`Global logout button ('${GLOBAL_CONFIG.LOGOUT_BUTTON_ID}') event listener attached.`);
    } else {
        // This can be helpful for debugging if you expect the button to be on every page
        // but it's not found on a particular one.
        // console.warn(`Global logout button with ID '${GLOBAL_CONFIG.LOGOUT_BUTTON_ID}' not found on this page.`);
    }

    // If you use Lucide icons globally (via data-lucide attributes) and
    // the Lucide library script is included on all pages, initialize them here.
    // Example:
    // if (typeof lucide !== 'undefined') {
    //     lucide.createIcons();
    //     console.log("Lucide icons initialized globally.");
    // }
}); */




// app/static/js/global_logout.js
// ... GLOBAL_CONFIG and handleGlobalLogout function ...

// This code runs after DOM is parsed because of 'defer'
const logoutButton = document.getElementById(GLOBAL_CONFIG.LOGOUT_BUTTON_ID);
if (logoutButton) {
    logoutButton.addEventListener('click', function(event) {
        event.preventDefault();
        handleGlobalLogout();
    });
    console.log(`Global logout button ('${GLOBAL_CONFIG.LOGOUT_BUTTON_ID}') event listener attached.`);
} else {
    // console.warn(...);
}
// if (typeof lucide !== 'undefined') { lucide.createIcons(); }