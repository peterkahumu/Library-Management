# Books App

The `books` app handles catalog data, inventory operations, and Google Books integration.

## Responsibilities

- Manage book metadata and stock levels.
- Enforce validation for copy counts and core fields.
- Provide browse/search/detail/create/edit views.
- Import books from Google Books API.

## Key Models

- `Genre`
- `Book`

## Key Views

- `BookListView`
- `BookDetailView`
- `BookCreateView`
- `BookEditView`
- `GoogleBooksSearchView`
- `GoogleBooksDetailView`
- `GoogleBooksAddView`

## Management Commands

- `python manage.py seed_genres`
- `python manage.py clear_cache`

## Inventory Behavior

- `borrow_book()` atomically decrements available copies.
- `return_book()` atomically increments available copies without exceeding total copies.
- Cache invalidation is triggered on inventory-affecting operations.
