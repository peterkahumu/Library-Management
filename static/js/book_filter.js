
// Filter functionality
const filterBadges = document.querySelectorAll('.filter-badge');
const bookItems = document.querySelectorAll('.book-item');
const resultCount = document.getElementById('resultCount');

filterBadges.forEach(badge => {
    badge.addEventListener('click', function () {
        const category = this.getAttribute('data-category');

        // Remove active class from all badges
        filterBadges.forEach(b => b.classList.remove('active'));
        // Add active class to clicked badge
        this.classList.add('active');

        let visibleCount = 0;

        // Filter books
        bookItems.forEach(book => {
            const bookCategories = book.getAttribute('data-category').toLowerCase().split(' ');

            if (category === 'all' || bookCategories.includes(category.toLowerCase())) {
                book.style.display = 'block';
                visibleCount++;
            } else {
                book.style.display = 'none';
            }
        });

        // Update count
        resultCount.textContent = visibleCount;
    });
});

// Search functionality
const searchInput = document.getElementById('searchInput');
searchInput.addEventListener('input', function () {
    const searchTerm = this.value.toLowerCase();
    let visibleCount = 0;

    bookItems.forEach(book => {
        const title = book.getAttribute('data-title').toLowerCase();
        const author = book.getAttribute('data-author').toLowerCase();

        if (title.includes(searchTerm) || author.includes(searchTerm)) {
            book.style.display = 'block';
            visibleCount++;
        } else {
            book.style.display = 'none';
        }
    });

    resultCount.textContent = visibleCount;
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

// Clear filters function
function clearFilters() {
    // Reset all filters
    filterBadges.forEach(b => b.classList.remove('active'));
    filterBadges[0].classList.add('active'); // Activate "All Books"

    // Show all books
    bookItems.forEach(book => {
        book.style.display = 'block';
    });

    // Reset search
    searchInput.value = '';

    // Update count
    resultCount.textContent = bookItems.length;
}
