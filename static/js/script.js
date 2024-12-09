document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('vehicle-form');
    const loadingSpinner = document.getElementById('loading-spinner');
    const yearInput = document.getElementById('year');
    const makeInput = document.getElementById('make');
    const modelInput = document.getElementById('model');
    const errorModal = document.getElementById('error-modal');
    const modalMessage = document.getElementById('modal-message');
    const closeModalButton = document.getElementById('close-modal');

    /**
     * Show the loading spinner
     */
    const showLoadingSpinner = () => loadingSpinner.classList.remove('hidden');

    /**
     * Hide the loading spinner
     */
    const hideLoadingSpinner = () => loadingSpinner.classList.add('hidden');

    /**
     * Show error modal with a custom message
     * @param {string} message - The error message to display
     */
    const showErrorModal = (message) => {
        modalMessage.textContent = message;
        errorModal.classList.remove('hidden');
    };

    /**
     * Close the error modal
     */
    closeModalButton.addEventListener('click', () => errorModal.classList.add('hidden'));

    /**
     * Validate required fields (year, make, model)
     * @returns {boolean} - True if fields are valid, false otherwise
     */
    const validateFields = () => {
        const year = yearInput.value.trim();
        const make = makeInput.value.trim();
        const model = modelInput.value.trim();

        if (!year || !make || !model) {
            showErrorModal('Year, Make, and Model fields are required.');
            hideLoadingSpinner();

            (!year ? yearInput : !make ? makeInput : modelInput).focus();
            return false;
        }
        return true;
    };

    /**
     * Restrict year input to 4 digits and numbers only
     */
    yearInput.addEventListener('input', () => {
        yearInput.value = yearInput.value.replace(/[^0-9]/g, '').slice(0, 4);
    });

    /**
     * Validate year range between 1960 and the current year + 1 (if after September)
     */
    yearInput.addEventListener('blur', () => {
        const year = parseInt(yearInput.value, 10);
        const currentDate = new Date();
        const maxYear = currentDate.getMonth() >= 8 ? currentDate.getFullYear() + 1 : currentDate.getFullYear();

        if (year < 1960 || year > maxYear) {
            showErrorModal(`Please enter a year between 1960 and ${maxYear}`);
            yearInput.value = '';
        }
    });

    /**
     * Handle form submission
     */
    form.addEventListener('submit', (event) => {
        showLoadingSpinner();

        if (!validateFields()) {
            event.preventDefault();
        }
    });
});
