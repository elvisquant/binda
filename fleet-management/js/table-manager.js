/*Generic, table rendering, search, pagination,export */
// js/table-manager.js
import { currentModuleConfig, apiRequest } from './spa.js'; // Import global config and apiRequest
import { openAddEditModal, openViewModal, openConfirmationModal, openInfoStatusModal } from './modal-manager.js';
import { getISODateString, getNestedProperty, debounce } from './utils.js'; // Import utilities

// DOM Elements (IDs from table-template.html)
let tableTitleElement, searchInput, addNewButton;
let filtersContainer, tableHeaderRow, tableBody, tableEmptyState;
let recordCountDisplay, paginationControls;

const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let currentTableData = [];
let currentSort = { key: null, direction: 'asc' }; // Default sort by ID if available

// Filter state
let activeDateFilterType = 'all'; // 'all', 'today', 'last7', 'last30', 'custom'
let customStartDate = null;
let customEndDate = null;
let activeStatusFilter = '';

// Store event listeners to remove them later
const eventListenersMap = new Map();

function addManagedEventListener(element, eventType, handler) {
    if (!element) return;
    element.addEventListener(eventType, handler);
    if (!eventListenersMap.has(element)) {
        eventListenersMap.set(element, []);
    }
    eventListenersMap.get(element).push({ type: eventType, handler });
}

export function clearTableEventListeners() {
    eventListenersMap.forEach((listeners, element) => {
        listeners.forEach(({ type, handler }) => {
            element.removeEventListener(type, handler);
        });
    });
    eventListenersMap.clear();
    // Also clear specific elements if needed
    if (filtersContainer) filtersContainer.innerHTML = '';
}


export async function initializeTableModule(config) { // config is currentModuleConfig from spa.js
    // Assign DOM elements (assumes they exist from table-template.html)
    tableTitleElement = document.getElementById('table-module-title');
    searchInput = document.getElementById('table-search-input');
    addNewButton = document.getElementById('add-new-record-button');
    filtersContainer = document.getElementById('table-filters-container');
    tableHeaderRow = document.getElementById('table-header-row');
    tableBody = document.getElementById('table-body-content');
    tableEmptyState = document.getElementById('table-empty-state');
    recordCountDisplay = document.getElementById('table-record-count-display');
    paginationControls = document.getElementById('table-pagination-controls');

    if (!tableBody) {
        console.error("Table body element not found. Cannot initialize table module.");
        return;
    }

    tableTitleElement.textContent = config.title || "Records";

    // Reset state for new module
    currentPage = 1;
    currentTableData = [];
    const idColumn = config.columns.find(c => c.isId);
    currentSort = { key: idColumn ? (idColumn.sortKey || idColumn.key) : (config.columns[0]?.sortKey || config.columns[0]?.key), direction: 'asc' };
    activeDateFilterType = 'all';
    customStartDate = null;
    customEndDate = null;
    activeStatusFilter = '';


    // Setup event listeners
    addManagedEventListener(addNewButton, 'click', () => openAddEditModal(config));
    addManagedEventListener(searchInput, 'input', debounce(handleSearch, 300));


    renderTableHeaders(config.columns);
    renderFilters(config); // Render date and status filters if configured

    await fetchDataAndRenderBody();
}

function renderTableHeaders(columnsConfig) {
    tableHeaderRow.innerHTML = ''; // Clear existing
    columnsConfig.forEach(col => {
        const th = document.createElement('th');
        th.className = 'py-3 px-3 font-semibold text-gray-600 dark:text-gray-300';
        th.textContent = col.header;
        if (col.sortable) {
            th.classList.add('cursor-pointer', 'hover:bg-gray-100', 'dark:hover:bg-gray-700');
            const sortIcon = document.createElement('i');
            sortIcon.className = 'ml-1.5 opacity-50';
            const sortKey = col.sortKey || col.key;
            if (currentSort.key === sortKey) {
                sortIcon.setAttribute('data-lucide', currentSort.direction === 'asc' ? 'arrow-up' : 'arrow-down');
                sortIcon.classList.remove('opacity-50');
            } else {
                sortIcon.setAttribute('data-lucide', 'unfold-vertical');
            }
            th.appendChild(sortIcon);
            addManagedEventListener(th, 'click', () => handleSort(sortKey));
        }
        tableHeaderRow.appendChild(th);
    });
    const actionsTh = document.createElement('th');
    actionsTh.className = 'py-3 px-3 font-semibold text-gray-600 dark:text-gray-300 text-center';
    actionsTh.textContent = 'Actions';
    tableHeaderRow.appendChild(actionsTh);
    lucide.createIcons({ nodes: [tableHeaderRow] });
}

function handleSort(sortKey) {
    if (currentSort.key === sortKey) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.key = sortKey;
        currentSort.direction = 'asc';
    }
    renderTableHeaders(currentModuleConfig.columns); // Re-render headers for icon update
    fetchDataAndRenderBody();
}


async function fetchDataAndRenderBody() {
    if (!currentModuleConfig || !currentModuleConfig.apiEndpoint) return;
    showLoadingSpinnerInTable(); // Show spinner within table body

    let queryParams = `skip=${(currentPage - 1) * ITEMS_PER_PAGE}&limit=${ITEMS_PER_PAGE}`;
    if (searchInput.value) {
        queryParams += `&search=${encodeURIComponent(searchInput.value)}`;
    }
    if (currentSort.key) {
        queryParams += `&ordering=${currentSort.direction === 'desc' ? '-' : ''}${currentSort.key}`;
    }

    // Apply date filters
    if (activeDateFilterType !== 'all') {
        let startDateStr, endDateStr;
        const today = new Date();
        if (activeDateFilterType === 'today') {
            startDateStr = getISODateString(today);
            endDateStr = getISODateString(today);
        } else if (activeDateFilterType === 'last7') {
            const sevenDaysAgo = new Date(today);
            sevenDaysAgo.setDate(today.getDate() - 6);
            startDateStr = getISODateString(sevenDaysAgo);
            endDateStr = getISODateString(today);
        } else if (activeDateFilterType === 'last30') {
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(today.getDate() - 29);
            startDateStr = getISODateString(thirtyDaysAgo);
            endDateStr = getISODateString(today);
        } else if (activeDateFilterType === 'custom' && customStartDate && customEndDate) {
            startDateStr = customStartDate;
            endDateStr = customEndDate;
        }
        if (startDateStr) queryParams += `&start_date=${startDateStr}`;
        if (endDateStr) queryParams += `&end_date=${endDateStr}`; // FastAPI typically uses start_date and end_date
    }

    // Apply status filter
    if (currentModuleConfig.statusFilterKey && activeStatusFilter) {
        queryParams += `&${currentModuleConfig.statusFilterKey}=${encodeURIComponent(activeStatusFilter)}`;
    }


    const result = await apiRequest(`${currentModuleConfig.apiEndpoint}?${queryParams}`);
    currentTableData = result && Array.isArray(result.items) ? result.items : []; // Assuming paginated response {items: [], total: X}
    const totalItems = result && typeof result.total === 'number' ? result.total : 0;

    renderTableBodyContent(currentTableData, currentModuleConfig.columns);
    renderPaginationControls(totalItems);
    updateRecordCountDisplay(totalItems);

    hideLoadingSpinnerInTable();
    tableEmptyState.classList.toggle('hidden', currentTableData.length > 0);
    document.getElementById('dynamic-crud-table').classList.toggle('hidden', currentTableData.length === 0);
}

function renderTableBodyContent(data, columnsConfig) {
    tableBody.innerHTML = ''; // Clear previous
    if (!data || data.length === 0) return;

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50 dark:hover:bg-gray-700/40 transition-colors';
        const itemId = getNestedProperty(item, columnsConfig.find(c => c.isId)?.key || 'id');

        columnsConfig.forEach(col => {
            const td = document.createElement('td');
            td.className = 'py-2.5 px-3';
            const value = getNestedProperty(item, col.key, col.fallback);
            td.innerHTML = (col.render && typeof window[col.render] === 'function')
                ? window[col.render](value, item)
                : (value === null || value === undefined ? (col.fallback || 'N/A') : value);
            tr.appendChild(td);
        });

        // Actions cell
        const actionsTd = document.createElement('td');
        actionsTd.className = 'py-2.5 px-3 text-center whitespace-nowrap';
        actionsTd.innerHTML = `
            <button data-action="view" data-id="${itemId}" class="text-blue-600 dark:text-blue-400 p-1.5 hover:bg-blue-100 dark:hover:bg-blue-900 rounded-md" title="View"><i data-lucide="eye" class="w-4 h-4"></i></button>
            <button data-action="edit" data-id="${itemId}" class="text-green-600 dark:text-green-400 p-1.5 hover:bg-green-100 dark:hover:bg-green-900 rounded-md ml-1" title="Edit"><i data-lucide="edit-3" class="w-4 h-4"></i></button>
            <button data-action="delete" data-id="${itemId}" class="text-red-600 dark:text-red-400 p-1.5 hover:bg-red-100 dark:hover:bg-red-900 rounded-md ml-1" title="Delete"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
        `;
        tr.appendChild(actionsTd);
        tableBody.appendChild(tr);
    });
    lucide.createIcons({ nodes: [tableBody] });
}

// Event delegation for table actions
addManagedEventListener(tableBody, 'click', (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;

    const action = button.dataset.action;
    const id = button.dataset.id;
    const itemData = currentTableData.find(item => String(getNestedProperty(item, currentModuleConfig.columns.find(c => c.isId)?.key || 'id')) === String(id));


    if (action === 'view') {
        openViewModal(currentModuleConfig, itemData);
    } else if (action === 'edit') {
        openAddEditModal(currentModuleConfig, id, itemData);
    } else if (action === 'delete') {
        handleDelete(id);
    }
});

function handleDelete(itemId) {
    openConfirmationModal(
        'Confirm Deletion',
        `Are you sure you want to delete this ${currentModuleConfig.title.replace(/Records|Record/i, '').trim().toLowerCase()} (ID: ${itemId})? This action cannot be undone.`,
        'Delete',
        'btn-danger', // Make sure .btn-danger is styled (e.g., bg-red-600)
        async (id) => {
            const result = await apiRequest(`${currentModuleConfig.apiEndpoint}${id}`, 'DELETE');
            if (result === true) { // DELETE returns 204, apiRequest maps to true
                openInfoStatusModal('Success', 'Record deleted successfully.', 'success');
                // If last item on a page > 1, go to previous page
                if (currentTableData.length === 1 && currentPage > 1) {
                    currentPage--;
                }
                fetchDataAndRenderBody();
            } else {
                openInfoStatusModal('Error', 'Failed to delete record. It might be in use or an error occurred.', 'error');
            }
        },
        itemId
    );
}


function handleSearch() {
    currentPage = 1;
    fetchDataAndRenderBody();
}


// Pagination, Record Count, Filters Rendering (next steps)
function renderPaginationControls(totalItems) {
    paginationControls.innerHTML = '';
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    if (totalPages <= 1) return;

    const createButton = (text, page, isDisabled = false, isActive = false, isIcon = false) => {
        const button = document.createElement('button');
        button.className = `px-3 py-1.5 text-sm rounded-md border dark:border-gray-600 transition-colors duration-150 focus:outline-none focus:ring-1 focus:ring-blue-500`;
        if (isDisabled) {
            button.disabled = true;
            button.className += ' bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 cursor-not-allowed';
        } else if (isActive) {
            button.className += ' bg-blue-600 text-white border-blue-600';
        } else {
            button.className += ' bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600';
        }
        if(isIcon) {
            button.innerHTML = `<i data-lucide="${text}" class="w-4 h-4"></i>`;
        } else {
            button.textContent = text;
        }
        addManagedEventListener(button, 'click', () => {
            currentPage = page;
            fetchDataAndRenderBody();
        });
        return button;
    };

    paginationControls.appendChild(createButton('chevron-left', currentPage - 1, currentPage === 1, false, true));

    // Simplified pagination links (e.g., 1 ... 5 6 7 ... 10)
    // For full complexity, a dedicated pagination function is better
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        paginationControls.appendChild(createButton(1, 1));
        if (startPage > 2) paginationControls.appendChild(createButton('...', currentPage, true)); // Disabled '...'
    }

    for (let i = startPage; i <= endPage; i++) {
        paginationControls.appendChild(createButton(i, i, false, i === currentPage));
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) paginationControls.appendChild(createButton('...', currentPage, true));
        paginationControls.appendChild(createButton(totalPages, totalPages));
    }

    paginationControls.appendChild(createButton('chevron-right', currentPage + 1, currentPage === totalPages, false, true));
    lucide.createIcons({ nodes: [paginationControls]});
}

function updateRecordCountDisplay(totalItems) {
    if (totalItems === 0) {
        recordCountDisplay.textContent = '0 records';
        return;
    }
    const startItem = (currentPage - 1) * ITEMS_PER_PAGE + 1;
    const endItem = Math.min(currentPage * ITEMS_PER_PAGE, totalItems);
    recordCountDisplay.textContent = `Showing ${startItem}-${endItem} of ${totalItems} records`;
}

function showLoadingSpinnerInTable() {
    const colSpan = tableHeaderRow.children.length || 5; // Default to 5 if headers not rendered yet
    tableBody.innerHTML = `<tr><td colspan="${colSpan}" class="text-center py-10"><div class="loader-container inline-block relative !inset-auto !bg-transparent"><div class="loader !w-8 !h-8 !border-4"></div></div></td></tr>`;
}
function hideLoadingSpinnerInTable() {
    // Fetch will replace the content, so explicit hide might not be needed
    // unless fetch fails and spinner remains. The general hideLoadingSpinner on main content area
    // should cover most cases.
}

function renderFilters(config) {
    filtersContainer.innerHTML = ''; // Clear previous
    let hasAnyFilter = false;

    // Date Filters
    if (config.hasDateFilters) {
        hasAnyFilter = true;
        const dateFilterGroup = document.createElement('div');
        dateFilterGroup.className = 'flex flex-col sm:flex-row items-start sm:items-center gap-2';
        dateFilterGroup.innerHTML = `
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">Date Range:</label>
            <div class="inline-flex rounded-md shadow-sm" role="group">
                <button data-date-filter="all" class="date-filter-btn active">All</button>
                <button data-date-filter="today" class="date-filter-btn">Today</button>
                <button data-date-filter="last7" class="date-filter-btn">Last 7D</button>
                <button data-date-filter="last30" class="date-filter-btn">Last 30D</button>
                <button data-date-filter="custom" class="date-filter-btn">Custom</button>
            </div>
            <div id="custom-date-inputs" class="hidden items-center gap-2 mt-2 sm:mt-0">
                <input type="date" id="custom-start-date" class="form-input-sm">
                <span class="text-sm dark:text-gray-400">to</span>
                <input type="date" id="custom-end-date" class="form-input-sm">
                <button id="apply-custom-date" class="btn btn-secondary btn-sm">Apply</button>
            </div>
        `;
        filtersContainer.appendChild(dateFilterGroup);
        // Add event listeners for date filter buttons
        dateFilterGroup.querySelectorAll('.date-filter-btn').forEach(btn => {
            addManagedEventListener(btn, 'click', handleDateFilterChange);
        });
        addManagedEventListener(document.getElementById('apply-custom-date'), 'click', applyCustomDateFilter);
    }

    // Status Filter
    if (config.statusFilterKey && config.statusFilterOptions) {
        hasAnyFilter = true;
        const statusFilterGroup = document.createElement('div');
        statusFilterGroup.className = 'flex flex-col sm:flex-row items-start sm:items-center gap-2';
        let optionsHtml = config.statusFilterOptions.map(opt => `<option value="${opt.value}">${opt.text}</option>`).join('');
        statusFilterGroup.innerHTML = `
            <label for="status-filter-select" class="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">Status:</label>
            <select id="status-filter-select" class="form-select-sm">
                ${optionsHtml}
            </select>
        `;
        filtersContainer.appendChild(statusFilterGroup);
        addManagedEventListener(document.getElementById('status-filter-select'), 'change', handleStatusFilterChange);
    }

    if (!hasAnyFilter) {
        filtersContainer.classList.add('hidden');
    } else {
        filtersContainer.classList.remove('hidden');
    }
    // Add Tailwind styles for .date-filter-btn, .form-input-sm, .form-select-sm, .btn-sm, .btn-secondary in your CSS or here
    // e.g., in css/style.css or a <style> tag in dashboard.html
    // .date-filter-btn { @apply px-3 py-1.5 text-xs border dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600; }
    // .date-filter-btn.active { @apply bg-blue-600 text-white border-blue-600 hover:bg-blue-700; }
    // .form-input-sm { @apply form-input !py-1.5 !text-xs; }
}

function handleDateFilterChange(event) {
    const btn = event.target.closest('.date-filter-btn');
    if (!btn) return;

    document.querySelectorAll('.date-filter-btn').forEach(b => b.classList.remove('active', 'bg-blue-600', 'text-white', 'border-blue-600'));
    btn.classList.add('active', 'bg-blue-600', 'text-white', 'border-blue-600'); // Add your active classes

    activeDateFilterType = btn.dataset.dateFilter;
    const customDateInputs = document.getElementById('custom-date-inputs');

    if (activeDateFilterType === 'custom') {
        customDateInputs.classList.remove('hidden');
        customDateInputs.classList.add('flex'); // Ensure it's flex for proper layout
    } else {
        customDateInputs.classList.add('hidden');
        customDateInputs.classList.remove('flex');
        customStartDate = null;
        customEndDate = null;
        currentPage = 1;
        fetchDataAndRenderBody();
    }
}

function applyCustomDateFilter() {
    const startInput = document.getElementById('custom-start-date');
    const endInput = document.getElementById('custom-end-date');
    if (startInput.value && endInput.value) {
        if (new Date(startInput.value) > new Date(endInput.value)) {
            openInfoStatusModal('Input Error', 'Start date cannot be after end date.', 'warning');
            return;
        }
        customStartDate = startInput.value;
        customEndDate = endInput.value;
        activeDateFilterType = 'custom'; // Ensure this is set
        currentPage = 1;
        fetchDataAndRenderBody();
    } else {
        openInfoStatusModal('Input Error', 'Please select both start and end dates for custom range.', 'warning');
    }
}

function handleStatusFilterChange(event) {
    activeStatusFilter = event.target.value;
    currentPage = 1;
    fetchDataAndRenderBody();
}

// Export functions that might be needed by spa.js, e.g., for form submission callbacks
// if not handled directly via event delegation or global handlers.
// For now, most interactions are internal or via modal-manager.