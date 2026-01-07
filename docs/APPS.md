# Application Documentation

This document provides detailed information about the Django applications within the Library Management System.

## Table of Contents
- [Accounts](#accounts)
- [Books](#books)
- [Book Circulation](#book-circulation)
- [Dashboards](#dashboards)
- [Pages](#pages)

---

## Accounts
**Path**: `accounts/`

Handles user authentication, registration, and profile management. It uses a custom user model `LibraryUser`.

### Models
**`LibraryUser`**
- Extends `AbstractUser`.
- **Fields**:
    - `user_id`: UUID, primary key.
    - `role`: Enum (`ADMIN`, `LIBRARIAN`, `STUDENT`).
    - `user_code`: Unique 10-char code (auto-generated).
    - `date_of_birth`: Date field.
    - `profile_image`: Image field.
    - `age`: Computed property.

### URLs
| Path | View | Name | Description |
| :--- | :--- | :--- | :--- |
| `accounts/register/` | `RegisterUserView` | `register` | User registration page. |
| `accounts/login/` | `LoginView` | `login` | *(Django Auth)* User login. |
| `accounts/logout/` | `LogoutView` | `logout` | *(Django Auth)* User logout. |

---

## Books
**Path**: `books/`

Manages the library inventory, including book details, genres, and availability.

### Models
**`Genre`**
- **Fields**: `name` (Choice field).

**`Book`**
- **Fields**:
    - `book_id`: UUID.
    - `title`, `author`, `isbn`, `description`.
    - `total_copies`, `copies_available`.
    - `format` (`HARDCOPY`, `EBOOK`, `AUDIOBOOK`).
    - `language`, `publication_date`.
- **Key Methods**:
    - `borrow_book()`: Decrements available copies.
    - `return_book()`: Increments available copies.

### URLs
| Path | View | Name | Description |
| :--- | :--- | :--- | :--- |
| `books/` | `BookListView` | `book_list` | List of all books with filters. |
| `books/<uuid:pk>/` | `BookDetailView` | `book_detail` | Detailed view of a specific book. |
| `books/new/` | `BookCreateView` | `book_create` | Add a new book (Admin/Librarian). |
| `books/<uuid:pk>/edit/` | `BookEditView` | `book_edit` | Edit an existing book. |

---

## Book Circulation
**Path**: `book_circulation/`

Handles the core business logic of borrowing and returning books.

### Models
**`Transaction`**
- Tracks the lifecycle of a book loan.
- **Fields**:
    - `status`: `PENDING`, `ISSUED`, `RETURN_REQUESTED`, `RETURNED`, `DOWNLOADED`.
    - `user`: ForeignKey to `LibraryUser`.
    - `book`: ForeignKey to `Book`.
    - `checkout_date`, `due_date`, `returned_date`.
- **Logic**:
    - Enforces valid status transitions.
    - Updates book inventory on specific transitions (e.g., `ISSUED` -> `RETURNED`).

### URLs
#### Student Actions
| Path | View | Name | Description |
| :--- | :--- | :--- | :--- |
| `circulation/borrow/<uuid:book_id>/` | `BorrowBookView` | `borrow_book` | Request to borrow a book. |
| `circulation/my-books/` | `MyBooksListView` | `my_books` | List of user's active/past loans. |
| `circulation/return-request/<uuid:pk>/` | `RequestReturnView` | `request_return` | Initiate return process. |

#### Librarian Actions
| Path | View | Name | Description |
| :--- | :--- | :--- | :--- |
| `circulation/librarian/borrow-requests/` | `LibrarianBorrowRequestsView` | `librarian_borrow_requests` | Manage pending borrow requests. |
| `circulation/librarian/return-requests/` | `LibrarianReturnRequestsView` | `librarian_return_requests` | Manage pending return requests. |
| `circulation/approve-borrow/<uuid:pk>/` | `ApproveBorrowView` | `approve_borrow` | Approve a borrow request. |
| `circulation/reject-borrow/<uuid:pk>/` | `RejectBorrowView` | `reject_borrow` | Reject a borrow request. |
| `circulation/approve-return/<uuid:pk>/` | `ApproveReturnView` | `approve_return` | Confirm book return. |
| `circulation/reject-return/<uuid:pk>/` | `RejectReturnView` | `reject_return` | Reject return (e.g., damaged). |

---

## Dashboards
**Path**: `dashboards/`

Provides role-specific landing pages and analytics.

### URLs
| Path | View | Name | Description |
| :--- | :--- | :--- | :--- |
| `dashboard/admin/` | `AdminDashboardView` | `admin_dashboard` | KPIs, Charts, User Management. |
| `dashboard/librarian/` | `LibrarianDashboardView` | `librarian_dashboard` | Operational metrics for librarians. |
| `dashboard/student/` | `StudentDashboardView` | `student_dashboard` | Personal stats for students. |
| `dashboard/logs/` | `TransactionLogsView` | `transaction_logs` | Detailed transaction history. |
| `dashboard/role-update/` | `UserRoleUpdateView` | `user_role_update` | Admin tool to change user roles. |

---

## Pages
**Path**: `pages/`

Static or semi-static pages.

### URLs
| Path | View | Name | Description |
| :--- | :--- | :--- | :--- |
| `/` | `HomeView` | `home` | Landing page. |
