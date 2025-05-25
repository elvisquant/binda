/*helper functions, e.g : date formatting,... */// js/utils.js
export function showLoadingSpinner(containerId = 'main-content-area') {
    const container = document.getElementById(containerId);
    if (!container) return;
    let spinnerDiv = container.querySelector('.loader-container');
    if (!spinnerDiv) {
        spinnerDiv = document.createElement('div');
        spinnerDiv.className = 'loader-container';
        spinnerDiv.innerHTML = '<div class="loader"></div>';
        // If container is not main-content-area, position relative might be needed on container
        if (containerId !== 'main-content-area' && getComputedStyle(container).position === 'static') {
            container.style.position = 'relative';
        }
        container.appendChild(spinnerDiv);
    }
    spinnerDiv.classList.remove('hidden');
}

export function hideLoadingSpinner(containerId = 'main-content-area') {
    const container = document.getElementById(containerId);
    const spinnerDiv = container?.querySelector('.loader-container');
    spinnerDiv?.classList.add('hidden');
}

export function getISODateTimeString(date) {
    if (!date) return null;
    const d = new Date(date);
    const pad = (num) => (num < 10 ? '0' : '') + num;
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function getISODateString(date) {
    if (!date) return null;
    const d = new Date(date);
    return `${d.getFullYear()}-${('0' + (d.getMonth() + 1)).slice(-2)}-${('0' + d.getDate()).slice(-2)}`;
}

// Example rendering functions (could be in table-manager.js or here)
export function formatDateTime(isoString) {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleString(navigator.language, { dateStyle: 'medium', timeStyle: 'short' });
    } catch (e) { return 'Invalid Date'; }
}

export function formatStatus(status) {
    if (!status) return 'N/A';
    return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
}

export function vehicleFullName(vehicleObj) {
    if (!vehicleObj || typeof vehicleObj !== 'object') return 'N/A';
    return `${vehicleObj.plate_number || 'N/A Plate'} (${vehicleObj.make || ''} ${vehicleObj.model || ''})`;
}

export function statusBadge(status, item) { // item can be used for more complex logic
    const statusFormatted = formatStatus(status);
    let colorClass = "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300"; // Default
    if (status) {
        switch (status.toLowerCase()) {
            case 'active': colorClass = "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100"; break;
            case 'inactive': case 'closed': colorClass = "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100"; break;
            case 'in_progress': case 'maintenance': colorClass = "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100"; break;
            case 'resolved': colorClass = "bg-blue-100 text-blue-700 dark:bg-blue-700 dark:text-blue-100"; break;
        }
    }
    return `<span class="px-2.5 py-0.5 text-xs font-medium rounded-full ${colorClass}">${statusFormatted}</span>`;
}

// Expose renderers to global scope if called directly from data-attributes string
window.formatDateTime = formatDateTime;
window.formatStatus = formatStatus;
window.vehicleFullName = vehicleFullName;
window.statusBadge = statusBadge;

// Debounce function
export function debounce(func, delay) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

// Get nested property utility
export function getNestedProperty(obj, path, fallback = undefined) {
    if (!path) return obj === undefined ? fallback : obj;
    const value = path.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : undefined, obj);
    return value === undefined ? fallback : value;
}



// js/utils.js (add these or similar)

// ... (existing utils like getISODateTimeString, etc.) ...

export function vehicleFullName(vehicleObj, item) { // item is the full row data
    // If vehicleObj is already the resolved object from API
    if (vehicleObj && typeof vehicleObj === 'object' && vehicleObj.plate_number) {
         return `${vehicleObj.plate_number} (${vehicleObj.make || ''} ${vehicleObj.model || ''})`;
    }
    // If vehicleObj is just an ID and you need to find it in item (less ideal for direct rendering)
    // Or if your API always returns the nested vehicle object directly.
    return 'N/A'; // Fallback
}

// statusBadge and formatStatus are likely already in your utils.js from previous examples

export function driverFullNameView(unusedValue, item) { // value might be empty if key is ""
    if (item && item.first_name && item.last_name) {
        return `${item.first_name} ${item.last_name}`;
    }
    return 'N/A';
}

export function formatCurrency(value, item, currency = 'USD') { // Default to USD or get from config
    if (typeof value !== 'number') return 'N/A';
    return new Intl.NumberFormat(navigator.language, { style: 'currency', currency: currency }).format(value);
}

export function formatDate(isoString) {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleDateString(navigator.language, {
            year: 'numeric', month: 'short', day: 'numeric'
        });
    } catch (e) { return 'Invalid Date'; }
}

// IMPORTANT: Expose renderers to global scope IF they are referenced as strings in data-* attributes
// and your table-manager.js or modal-manager.js looks for them on `window`.
window.vehicleFullName = vehicleFullName;
window.statusBadge = statusBadge; // Assuming it's defined elsewhere in utils.js
window.formatDateTime = formatDateTime; // Assuming it's defined
window.formatStatus = formatStatus; // Assuming it's defined
window.driverFullNameView = driverFullNameView;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;