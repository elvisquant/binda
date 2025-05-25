/*Generic modal handling, form generation*/
// js/modal-manager.js
import { apiRequest } from './spa.js'; // For API lookups in forms
import { getISODateTimeString, getNestedProperty } from './utils.js';

// Modal Elements (assuming these IDs are in dashboard.html)
const addEditModal = document.getElementById('genericAddEditModal');
const viewModal = document.getElementById('genericViewModal');
const confirmModal = document.getElementById('genericConfirmModal');
const infoStatusModal = document.getElementById('infoStatusModal');

// Add/Edit Modal specific elements
const genericModalTitle = document.getElementById('genericModalTitle');
const genericModalSubtitle = document.getElementById('genericModalSubtitle');
const genericAddEditForm = document.getElementById('genericAddEditForm');
const genericFormFieldsContainer = document.getElementById('genericFormFieldsContainer');
const itemIdFormInput = document.getElementById('itemId_form'); // Hidden input for ID
const genericSubmitButton = document.getElementById('genericSubmitButton');

// View Modal specific elements
const genericViewModalTitle = document.getElementById('genericViewModalTitle');
const genericViewDetailsContainer = document.getElementById('genericViewDetailsContainer');

// Confirm Modal specific elements
const genericConfirmModalTitle = document.getElementById('genericConfirmModalTitle');
const genericConfirmModalMessage = document.getElementById('genericConfirmModalMessage');
const genericConfirmModalConfirmBtn = document.getElementById('genericConfirmModalConfirmBtn');

// Info/Status Modal specific elements
const infoStatusModalTitle = document.getElementById('infoStatusModalTitle');
const infoStatusModalMessage = document.getElementById('infoStatusModalMessage');
const infoStatusModalIconContainer = document.getElementById('infoStatusModalIconContainer');
const infoStatusModalOkButton = document.getElementById('infoStatusModalOkButton');


let currentConfirmActionCallback = null;
let currentConfirmActionData = null;
let infoStatusModalTimeout = null;


export function openModal(modalElement) {
    if (modalElement) {
        modalElement.classList.remove('hidden');
        document.body.classList.add('overflow-hidden'); // Prevent background scroll
    }
}

export function closeModal(modalElement) {
    if (modalElement) {
        modalElement.classList.add('hidden');
        // Only remove overflow-hidden if no other modals are open
        const anyModalOpen = document.querySelector('.modal:not(.hidden)');
        if (!anyModalOpen) {
            document.body.classList.remove('overflow-hidden');
        }
    }
}
export function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => closeModal(m));
}


// --- Add/Edit Modal Logic ---
export async function openAddEditModal(config, itemId = null, currentData = null) {
    const isEditMode = itemId !== null;
    itemIdFormInput.value = isEditMode ? itemId : '';
    genericModalTitle.textContent = `${isEditMode ? 'Edit' : 'Add New'} ${config.title.replace(/Records|Record/i, '').trim()}`;
    genericModalSubtitle.textContent = isEditMode ? `Update details for ID: ${itemId}` : `Enter details for the new item.`;

    genericSubmitButton.innerHTML = `<i data-lucide="${isEditMode ? 'save' : 'plus-circle'}" class="w-4 h-4 mr-1.5"></i> ${isEditMode ? 'Save Changes' : 'Add Record'}`;
    lucide.createIcons({ nodes: [genericSubmitButton] }); // Re-render icon

    await populateFormFields(config.formFields, isEditMode ? currentData : {});
    openModal(addEditModal);
}

async function populateFormFields(formFieldsConfig, dataToEdit = {}) {
    genericFormFieldsContainer.innerHTML = ''; // Clear previous fields

    for (const field of formFieldsConfig) {
        const fieldWrapper = document.createElement('div');
        const label = document.createElement('label');
        label.htmlFor = field.id;
        label.className = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';
        label.innerHTML = `${field.label}${field.required ? '<span class="text-red-500 ml-0.5">*</span>' : ''}`;
        fieldWrapper.appendChild(label);

        let inputElement;
        const existingValue = getNestedProperty(dataToEdit, field.id, field.defaultValue !== undefined ? field.defaultValue : '');


        switch (field.type) {
            case 'select':
                inputElement = document.createElement('select');
                inputElement.innerHTML = `<option value="">${field.placeholder || `Select ${field.label}`}</option>`;
                if (field.options) {
                    field.options.forEach(opt => {
                        const option = new Option(opt.text, opt.value);
                        if (String(existingValue) === String(opt.value)) option.selected = true;
                        inputElement.add(option);
                    });
                } else if (field.apiLookup) {
                    const lookupData = await apiRequest(field.apiLookup);
                    if (lookupData && Array.isArray(lookupData)) {
                        lookupData.forEach(item => {
                            const value = item[field.valueField];
                            const text = field.displayFields.map(df => getNestedProperty(item, df, '')).join(' - ');
                            const option = new Option(text, value);
                            // Use original ID from dataToEdit (e.g. vehicle_id instead of just vehicle object)
                            const idFieldKey = field.id.endsWith('_id') ? field.id : `${field.id}_id`;
                            const selectedValueFromData = getNestedProperty(dataToEdit, idFieldKey);

                            if (selectedValueFromData !== undefined && String(selectedValueFromData) === String(value)) {
                                option.selected = true;
                            } else if (existingValue && typeof existingValue === 'object' && String(existingValue[field.valueField]) === String(value)) {
                                // Handle case where existingValue is an object containing the ID
                                option.selected = true;
                            }
                            inputElement.add(option);
                        });
                    }
                }
                break;
            case 'textarea':
                inputElement = document.createElement('textarea');
                inputElement.rows = field.rows || 3;
                inputElement.value = existingValue;
                if (field.placeholder) inputElement.placeholder = field.placeholder;
                break;
            default: // text, number, email, password, date, datetime-local
                inputElement = document.createElement('input');
                inputElement.type = field.type;
                if (field.type === 'datetime-local') {
                    inputElement.value = existingValue ? getISODateTimeString(new Date(existingValue)) : (field.defaultToNow ? getISODateTimeString(new Date()) : '');
                } else {
                    inputElement.value = existingValue;
                }
                if (field.placeholder) inputElement.placeholder = field.placeholder;
        }

        inputElement.id = field.id;
        inputElement.name = field.id; // Ensure name attribute for FormData
        inputElement.className = 'form-input w-full px-3 py-2 text-sm border dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white focus:ring-blue-500 focus:border-blue-500';
        if (field.required) inputElement.required = true;

        fieldWrapper.appendChild(inputElement);
        genericFormFieldsContainer.appendChild(fieldWrapper);
    }
}


// --- View Modal Logic ---
export function openViewModal(config, itemData) {
    genericViewModalTitle.textContent = `${config.title.replace(/Records|Record/i, '').trim()} Details`;
    genericViewDetailsContainer.innerHTML = ''; // Clear previous

    let detailsHtml = '<dl class="divide-y dark:divide-gray-700">';
    config.viewFields.forEach(field => {
        const value = getNestedProperty(itemData, field.key, field.fallback || 'N/A');
        const displayValue = (field.render && typeof window[field.render] === 'function')
            ? window[field.render](value, itemData) // Pass full itemData for context if needed
            : (value === null || value === undefined ? 'N/A' : value);

        detailsHtml += `
            <div class="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">${field.label}</dt>
                <dd class="mt-1 text-sm text-gray-900 dark:text-white sm:mt-0 sm:col-span-2 whitespace-pre-wrap">${displayValue}</dd>
            </div>
        `;
    });
    detailsHtml += '</dl>';
    genericViewDetailsContainer.innerHTML = detailsHtml;
    lucide.createIcons({ nodes: [genericViewDetailsContainer] }); // If any icons are in rendered values
    openModal(viewModal);
}


// --- Confirmation Modal Logic ---
export function openConfirmationModal(title, message, confirmButtonText = 'Confirm', confirmButtonClass = 'btn-primary', onConfirm, actionData = null) {
    genericConfirmModalTitle.textContent = title;
    genericConfirmModalMessage.innerHTML = message; // Use innerHTML for potential simple formatting
    genericConfirmModalConfirmBtn.textContent = confirmButtonText;
    genericConfirmModalConfirmBtn.className = `btn ${confirmButtonClass} w-full sm:w-auto`; // Reset and apply new classes

    currentConfirmActionCallback = onConfirm;
    currentConfirmActionData = actionData;
    openModal(confirmModal);
}


// --- Info/Status Modal Logic ---
export function openInfoStatusModal(title, message, type = 'success', autoCloseDelay = 3000) {
    infoStatusModalTitle.textContent = title;
    infoStatusModalMessage.innerHTML = message; // Use innerHTML

    let iconName = 'info', iconColorClass = 'text-blue-500', bgColorClass = 'bg-blue-100 dark:bg-blue-900';
    if (type === 'success') {
        iconName = 'check-circle-2'; iconColorClass = 'text-green-500'; bgColorClass = 'bg-green-100 dark:bg-green-900';
    } else if (type === 'error') {
        iconName = 'x-circle'; iconColorClass = 'text-red-500'; bgColorClass = 'bg-red-100 dark:bg-red-900';
    } else if (type === 'warning') {
        iconName = 'alert-triangle'; iconColorClass = 'text-yellow-500'; bgColorClass = 'bg-yellow-100 dark:bg-yellow-900';
    }
    infoStatusModalIconContainer.className = `mx-auto flex items-center justify-center h-12 w-12 rounded-full ${bgColorClass} mb-4`;
    infoStatusModalIconContainer.innerHTML = `<i data-lucide="${iconName}" class="h-7 w-7 ${iconColorClass}"></i>`;
    lucide.createIcons({ nodes: [infoStatusModalIconContainer] });

    openModal(infoStatusModal);
    if (infoStatusModalTimeout) clearTimeout(infoStatusModalTimeout);
    if (autoCloseDelay > 0) {
        infoStatusModalTimeout = setTimeout(() => closeModal(infoStatusModal), autoCloseDelay);
    }
}


// Event Listeners for Modal Close Buttons (attach once in spa.js on DOMContentLoaded)
export function initializeModalEventListeners() {
    // Add/Edit Modal
    document.getElementById('closeGenericAddEditModalButtonTop')?.addEventListener('click', () => closeModal(addEditModal));
    document.getElementById('cancelGenericAddEditModalButton')?.addEventListener('click', () => closeModal(addEditModal));
    addEditModal?.addEventListener('click', (e) => { if (e.target === addEditModal) closeModal(addEditModal); }); // Click outside to close

    // View Modal
    document.getElementById('closeGenericViewModalButtonTop')?.addEventListener('click', () => closeModal(viewModal));
    document.getElementById('closeGenericViewModalButtonBottom')?.addEventListener('click', () => closeModal(viewModal));
    viewModal?.addEventListener('click', (e) => { if (e.target === viewModal) closeModal(viewModal); });

    // Confirm Modal
    document.getElementById('closeGenericConfirmModalButtonX')?.addEventListener('click', () => closeModal(confirmModal));
    document.getElementById('cancelGenericConfirmModalButton')?.addEventListener('click', () => closeModal(confirmModal));
    genericConfirmModalConfirmBtn?.addEventListener('click', () => {
        if (typeof currentConfirmActionCallback === 'function') {
            currentConfirmActionCallback(currentConfirmActionData);
        }
        closeModal(confirmModal);
    });
    confirmModal?.addEventListener('click', (e) => { if (e.target === confirmModal) closeModal(confirmModal); });


    // Info/Status Modal
    infoStatusModalOkButton?.addEventListener('click', () => closeModal(infoStatusModal));
    infoStatusModal?.addEventListener('click', (e) => { if (e.target === infoStatusModal) closeModal(infoStatusModal); });

}

// Call initializeModalEventListeners from spa.js DOMContentLoaded





// js/modal-manager.js (add this function)
// This function can be called from anywhere (e.g., dashboard-overview.js or spa.js)
// It finds the nav link for the target module and simulates the data needed by openAddEditModal
export function triggerAddForModule(targetModuleName) {
    const navList = document.getElementById('main-nav-list');
    if (!navList) {
        console.error("Main nav list not found for triggerAddForModule");
        return;
    }
    const targetNavLink = navList.querySelector(`.nav-link[data-module="${targetModuleName}"]`);
    if (!targetNavLink) {
        console.error(`Nav link for module "${targetModuleName}" not found.`);
        openInfoStatusModal("Error", `Configuration for module '${targetModuleName}' not found for Quick Add.`, "error");
        return;
    }

    // Construct a temporary config object from the nav link's data attributes
    // This is similar to what spa.js does in loadContent
    const tempConfig = {
        name: targetModuleName,
        title: targetNavLink.dataset.title || 'New Item',
        apiEndpoint: targetNavLink.dataset.apiEndpoint,
        formFields: targetNavLink.dataset.formFields ? JSON.parse(targetNavLink.dataset.formFields) : [],
        // We only need formFields for adding
    };

    if (!tempConfig.apiEndpoint || tempConfig.formFields.length === 0) {
        console.error(`Module "${targetModuleName}" is missing apiEndpoint or formFields configuration for Quick Add.`);
        openInfoStatusModal("Error", `Cannot Quick Add for '${targetModuleName}'. Missing configuration.`, "error");
        return;
    }

    // Now call the existing openAddEditModal function
    openAddEditModal(tempConfig, null, {}); // null for itemId (add mode), empty object for dataToEdit
}