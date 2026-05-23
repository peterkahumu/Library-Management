document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-percent-display]").forEach((display) => {
        const trait = display.getAttribute("data-percent-display");
        const slider = document.querySelector(`[name="${trait}"]`);

        if (!slider) {
            return;
        }

        const updateDisplay = () => {
            const percentage = Math.round(Number(slider.value || 0) * 100);
            display.textContent = `${percentage}%`;
        };

        updateDisplay();
        slider.addEventListener("input", updateDisplay);
        slider.addEventListener("change", updateDisplay);
    });
});
