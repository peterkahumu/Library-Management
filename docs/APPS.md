# Application Documentation

This document summarizes the responsibilities of each module in the project.

## Django Apps

### Accounts
Path: `accounts/`

Responsibilities:
- Custom user model (`LibraryUser`) with UUID primary key.
- Role support (`admin`, `librarian`, `student`).
- User registration flow.

URLs:
- `accounts/register/` -> `RegisterUserView` (`register`)
- Auth routes from Django are also mounted under `accounts/` (`login`, `logout`, password flows).

Management commands:
- `python manage.py seed_superuser`

### Books
Path: `books/`

Responsibilities:
- Book and genre catalog management.
- Inventory validation and stock operations.
- Google Books search/detail/import integration.

Key models:
- `Genre`
- `Book`

URLs:
- `books/` -> `BookListView` (`book_list`)
- `books/<uuid:pk>/` -> `BookDetailView` (`book_detail`)
- `books/new/` -> `BookCreateView` (`book_create`)
- `books/<uuid:pk>/edit/` -> `BookEditView` (`book_edit`)
- `books/google-books/search/` -> `GoogleBooksSearchView` (`google_books_search`)
- `books/google-books/detail/<str:volume_id>/` -> `GoogleBooksDetailView` (`google_books_detail`)
- `books/google-books/add/<str:volume_id>/` -> `GoogleBooksAddView` (`google_books_add`)

Management commands:
- `python manage.py seed_genres`
- `python manage.py clear_cache`

### Book Circulation
Path: `book_circulation/`

Responsibilities:
- Borrowing and return lifecycle management.
- Transaction state validation and transitions.
- Physical and digital checkout flows.

Key model:
- `Transaction` with statuses:
  - `PENDING`
  - `ISSUED`
  - `DOWNLOADED`
  - `RETURN_REQUESTED`
  - `RETURNED`

URLs:
- `circulation/borrow/<uuid:book_id>/` -> `BorrowBookView` (`borrow_book`)
- `circulation/my-books/` -> `MyBooksListView` (`my_books`)
- `circulation/return-request/<uuid:pk>/` -> `RequestReturnView` (`request_return`)
- `circulation/librarian/borrow-requests/` -> `LibrarianBorrowRequestsView` (`librarian_borrow_requests`)
- `circulation/librarian/return-requests/` -> `LibrarianReturnRequestsView` (`librarian_return_requests`)
- `circulation/approve-borrow/<uuid:pk>/` -> `ApproveBorrowView` (`approve_borrow`)
- `circulation/reject-borrow/<uuid:pk>/` -> `RejectBorrowView` (`reject_borrow`)
- `circulation/approve-return/<uuid:pk>/` -> `ApproveReturnView` (`approve_return`)
- `circulation/reject-return/<uuid:pk>/` -> `RejectReturnView` (`reject_return`)

### Dashboards
Path: `dashboards/`

Responsibilities:
- Role-specific dashboards.
- KPI/analytics views and transaction log filtering.
- Admin user role updates.

URLs:
- `dashboard/admin/` -> `AdminDashboardView` (`admin_dashboard`)
- `dashboard/librarian/` -> `LibrarianDashboardView` (`librarian_dashboard`)
- `dashboard/student/` -> `StudentDashboardView` (`student_dashboard`)
- `dashboard/logs/` -> `TransactionLogsView` (`transaction_logs`)
- `dashboard/role-update/` -> `UserRoleUpdateView` (`user_role_update`)

### Pages
Path: `pages/`

Responsibilities:
- Public home page for anonymous users.
- Role-based redirect for authenticated users.

URL:
- `/` -> `HomeView` (`home`)

## Supporting Modules

### Caching
Path: `caching/`

Responsibilities:
- Cache key constants and TTL values.
- Cache-backed retrieval for homepage stats, genres, related books, and dashboard KPIs.
- Invalidation helpers used by signals and utilities.

### Communications
Path: `communications/`

Responsibilities:
- Centralized email sending for borrowing/return events via `LibraryEmailService`.

### AI Service
Path: `ai_service/`

Responsibilities:
- FastAPI chat service for LibraBot.
- SSE endpoint `POST /chat/stream` and health endpoint `GET /health`.

The Django frontend includes chatbot UI in `templates/components/chatbot.html` and uses `static/js/chatbot.js` to call the AI service.
