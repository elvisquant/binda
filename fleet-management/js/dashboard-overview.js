// js/dashboard-overview.js

// Re-declare or import your mock data or API fetch logic for dashboard overview
function generateMonthlyLabels(count, refEndDate = new Date()) { /* ... as before ... */ }
const mockDashboardData = { /* ... as before ... */ };

let monthlyActivityChartInstance = null;
let vehicleStatusChartInstance = null;

function updateKPIs(kpiData) {
    // Use try-catch or conditional checks for elements in case they don't exist
    document.getElementById('kpiTotalVehicles')?.textContent = kpiData.totalVehicles;
    const tvChangeEl = document.getElementById('kpiTotalVehiclesChange');
    if (tvChangeEl) {
        tvChangeEl.textContent = kpiData.totalVehiclesChange;
        tvChangeEl.className = `text-xs mt-0.5 ${kpiData.totalVehiclesChangeType === 'positive' ? 'text-green-500 dark:text-green-400' : kpiData.totalVehiclesChangeType === 'negative' ? 'text-red-500 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`;
    }
    // ... update other KPIs similarly ...
    document.getElementById('kpiActiveTrips')?.textContent = kpiData.activeTrips;
    // ...
    document.getElementById('kpiRepairsMonth')?.textContent = kpiData.repairsMonth;
    // ...
    document.getElementById('kpiFuelCostToday')?.textContent = `$${kpiData.fuelCostToday}`;
    // ...
}

function updateKPIsForDate(selectedDate) {
    // Your existing logic to regenerate KPI data based on date
    const dateSeed = new Date(selectedDate).getDate();
    const newKpis = { /* ... your logic ... */ };
    updateKPIs(newKpis);
}

function initializeDashboardCharts(isThemeChange = false, monthlyData, statusData) {
    const isDarkMode = document.documentElement.classList.contains('dark');
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)';
    const labelColor = isDarkMode ? 'rgba(229, 231, 235, 0.8)' : 'rgba(55, 65, 81, 0.8)';
    const tooltipBgColor = isDarkMode ? 'rgba(31, 41, 55, 0.9)' : 'rgba(255, 255, 255, 0.9)';
    const tooltipTitleColor = isDarkMode ? '#f3f4f6' : '#1f2937';
    const tooltipBodyColor = isDarkMode ? '#d1d5db' : '#4b5563';

    // Access Tailwind colors (if you need them in JS and stored them on window.tailwindConfig)
    // const primaryDefault = window.tailwindConfig?.theme.extend.colors.primary.DEFAULT || '#3b82f6';
    // Or use direct hex/rgb values if simpler and they are stable
    const primaryDefault = '#3b82f6';
    const secondaryDefault = '#10b981';
    const warningDefault = '#f59e0b';

    const monthlyCtx = document.getElementById('monthlyActivityChart')?.getContext('2d');
    if (monthlyCtx) {
        if (monthlyActivityChartInstance) monthlyActivityChartInstance.destroy();
        monthlyActivityChartInstance = new Chart(monthlyCtx, { /* ... your chart config ... */ });
    }

    const statusCtx = document.getElementById('vehicleStatusChart')?.getContext('2d');
    if (statusCtx) {
        if (vehicleStatusChartInstance) vehicleStatusChartInstance.destroy();
        const totalStatus = statusData.data.reduce((a,b) => a+b, 0);
        vehicleStatusChartInstance = new Chart(statusCtx, { /* ... your chart config ... */ });
    }
}

function handleQuickAddDropdown() {
    const quickAddBtn = document.getElementById('quickAddBtn');
    const quickAddDropdown = document.getElementById('quickAddDropdown');
    if(quickAddBtn && quickAddDropdown) {
        const toggle = () => quickAddDropdown.classList.toggle('hidden');
        const close = () => quickAddDropdown.classList.add('hidden');

        quickAddBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggle();
        });
        // Handle clicks on quick add links (to open generic modals)
        quickAddDropdown.querySelectorAll('.quick-add-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                close();
                const targetModule = link.dataset.targetModule;
                // You'll need a global way to trigger the add modal for a specific module
                // This might involve finding the nav link for that module and simulating a click
                // or directly calling a function in modal-manager.js if it's adapted for this.
                console.log(`Quick add for: ${targetModule}`);
                // Example: window.spa.triggerModuleAdd(targetModule); // (spa.js would need this function)
                // For now, just log it.
                if (window.modalManager && typeof window.modalManager.triggerAddForModule === 'function') {
                    window.modalManager.triggerAddForModule(targetModule);
                } else {
                     alert(`TODO: Implement quick add for ${targetModule}. modalManager or trigger function not found.`);
                }
            });
        });
        // Global click to close dropdown
        document.addEventListener('click', (event) => {
            if (quickAddBtn && !quickAddBtn.contains(event.target) && quickAddDropdown && !quickAddDropdown.contains(event.target)) {
                close();
            }
        });
    }
}


// This is the main function spa.js will call for this module
export function initializeDashboardOverviewModule() {
    console.log("Initializing Dashboard Overview Module...");
    updateKPIs(mockDashboardData.kpis);
    initializeDashboardCharts(false, mockDashboardData.monthlyActivity, mockDashboardData.vehicleStatus);

    const dashboardDateFilter = document.getElementById('dashboardDateFilter');
    if (dashboardDateFilter) {
        const today = new Date().toISOString().split('T')[0];
        dashboardDateFilter.value = today;
        // Remove old listener if any, or ensure it's added once
        dashboardDateFilter.removeEventListener('change', handleDateFilterEvent); // Prevent multiple listeners
        dashboardDateFilter.addEventListener('change', handleDateFilterEvent);
    }

    handleQuickAddDropdown();
    // Any other specific initializations for dashboard-overview.html
}

function handleDateFilterEvent(event) { // Named function for removal
    console.log("Dashboard date filter changed to:", event.target.value);
    updateKPIsForDate(event.target.value);
    // Potentially re-fetch chart data for this date
}

// Function to be called when the theme changes (if charts need explicit redraw)
export function handleDashboardOverviewThemeChange() {
    if (monthlyActivityChartInstance || vehicleStatusChartInstance) {
        console.log("Dashboard Overview: Handling theme change for charts.");
        initializeDashboardCharts(true, mockDashboardData.monthlyActivity, mockDashboardData.vehicleStatus);
    }
}

// Optional: Cleanup function if this module needs to remove listeners or destroy charts
export function cleanupDashboardOverviewModule() {
    console.log("Cleaning up Dashboard Overview Module...");
    if (monthlyActivityChartInstance) {
        monthlyActivityChartInstance.destroy();
        monthlyActivityChartInstance = null;
    }
    if (vehicleStatusChartInstance) {
        vehicleStatusChartInstance.destroy();
        vehicleStatusChartInstance = null;
    }
    // Remove specific event listeners if they were added directly here
    const dashboardDateFilter = document.getElementById('dashboardDateFilter');
    if (dashboardDateFilter) {
        dashboardDateFilter.removeEventListener('change', handleDateFilterEvent);
    }
    // Remove quick add listeners if needed, though a global click listener might be fine
}