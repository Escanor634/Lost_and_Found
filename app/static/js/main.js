/**
 * Campus Lost & Found - Client-side Utilities
 */
document.addEventListener("DOMContentLoaded", () => {
    // Initialize Bootstrap tooltips if any
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.forEach((tooltipTriggerEl) => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss success flash alerts after 6 seconds
    const successAlerts = document.querySelectorAll(".alert-success");
    successAlerts.forEach((alertEl) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            bsAlert.close();
        }, 6000);
    });

    // Prevent double form submissions on primary submit buttons
    const forms = document.querySelectorAll("form");
    forms.forEach((form) => {
        form.addEventListener("submit", (e) => {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn && form.checkValidity()) {
                submitBtn.setAttribute("data-submitting", "true");
            }
        });
    });
});
