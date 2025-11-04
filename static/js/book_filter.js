const resultCount = document.getElementById('resultCount');
const filterBadges = document.querySelectorAll('.filter-badge');
const genreInput = document.getElementById('genreInput');
const filterForm = document.getElementById('filterForm');
const searchInput = document.getElementById('searchInput');

// Filter by genre
filterBadges.forEach(badge => {
    badge.addEventListener('click', () => {
        filterBadges.forEach(b => b.classList.remove('active'));
        badge.classList.add('active');
        genreInput.value = badge.dataset.category;
        filterForm.submit();
    });
});

// Debounced live search
let typingTimer;
searchInput.addEventListener('input', () => {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => filterForm.submit(), 1500);
});

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const activeGenre = params.get('genre');
    const badges = document.querySelectorAll('.filter-badge');

    badges.forEach(badge => {
        badge.classList.remove('active');
        if (!activeGenre && badge.dataset.category === 'all') {
            badge.classList.add('active');
        } else if (badge.dataset.category.toLowerCase() === activeGenre?.toLowerCase()) {
            badge.classList.add('active');
        }
    });
});


// Sort functionality
const sortSelect = document.getElementById('sortSelect');
sortSelect.addEventListener('change', function () {
    const sortBy = this.value;
    const container = document.getElementById('booksContainer');
    const items = Array.from(bookItems);

    items.sort((a, b) => {
        if (sortBy === 'title') {
            return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title'));
        } else if (sortBy === 'author') {
            return a.getAttribute('data-author').localeCompare(b.getAttribute('data-author'));
        }
        // For 'year' and 'popular', maintain current order for demo
        return 0;
    });

    // Re-append sorted items
    items.forEach(item => container.appendChild(item));
});

// Set initial active filter
filterBadges[0].classList.add('active')


function clearFilters() {
    // Reset genre selection
    genreInput.value = 'all';
    searchInput.value = '';

    filterForm.submit();
}
