document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const tabName = urlParams.get('tab');
    if (tabName) {
        const tabEl = document.querySelector(`#pills-${tabName}-tab`);
        if (tabEl) {
            const tab = new bootstrap.Tab(tabEl);
            tab.show();
        }
    }
});
