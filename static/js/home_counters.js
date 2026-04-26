document.addEventListener("DOMContentLoaded", () => {
    const counters = document.querySelectorAll("[data-count]");
    counters.forEach(counter => {
        const updateCount = () => {
            const target = +counter.getAttribute("data-count");
            const count = +counter.innerText;
            const increment = target / 100;
            if (count < target) {
                counter.innerText = Math.ceil(count + increment);
                setTimeout(updateCount, 30);
            } else {
                counter.innerText = target.toLocaleString();
            }
        };
        updateCount();
    });
});
