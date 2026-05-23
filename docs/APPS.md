# Application Documentation

This file documents the Django apps that make up the `library-management` project and notes other services in the repository.

**Django Apps**

- **Accounts**: Path: [library-management/accounts](library-management/accounts)
  - **Responsibilities:** Custom user model (`LibraryUser`) with UUID primary key, role-based access (`admin`, `librarian`, `student`), profile image and `PersonalityProfile`, custom user manager, admin forms and signals.
  - **Key files:** [library-management/accounts/models.py](library-management/accounts/models.py), [library-management/accounts/admin.py](library-management/accounts/admin.py), [library-management/accounts/apps.py](library-management/accounts/apps.py)

- **Books**: Path: [library-management/books](library-management/books)
  - **Responsibilities:** Book and genre models, inventory (stock) operations and validation, embeddings (`pgvector`), Google Books integration for search/import, cache invalidation helpers.
  - **Key files:** [library-management/books/models.py](library-management/books/models.py), [library-management/books/google_books.py](library-management/books/google_books.py)

- **Book Circulation**: Path: [library-management/book_circulation](library-management/book_circulation)
  - **Responsibilities:** Borrow/return lifecycle, transaction/state management, atomic stock updates for hard copies, separate handling for e-books.
  - **Key files:** [library-management/book_circulation/models.py](library-management/book_circulation/models.py), [library-management/book_circulation/admin.py](library-management/book_circulation/admin.py)

- **Dashboards**: Path: [library-management/dashboards](library-management/dashboards)
  - **Responsibilities:** Role-specific dashboards (admin, librarian, student), KPIs and transaction log views.
  - **Key files:** [library-management/dashboards/views.py](library-management/dashboards/views.py)

- **Pages**: Path: [library-management/pages](library-management/pages)
  - **Responsibilities:** Public site pages and the project home view; lightweight content app used for anonymous/home pages and redirects.
  - **Key files:** [library-management/pages/views.py](library-management/pages/views.py)

**Supporting Modules**

- **Caching**: Path: [library-management/caching](library-management/caching)
  - **Responsibilities:** Cache key definitions, TTLs, helpers and services used to cache homepage stats, genre lists, related books and to invalidate caches when models change.
  - **Key files:** [library-management/caching/services.py](library-management/caching/services.py), [library-management/caching/keys.py](library-management/caching/keys.py)

- **Communications**: Path: [library-management/communications](library-management/communications)
  - **Responsibilities:** Centralized email utilities used for notifications (borrowing, returns, admin alerts).
  - **Key files:** [library-management/communications/email.py](library-management/communications/email.py)

**Project core & static assets**

- **Project settings**: Path: [library-management/LibraryManagement](library-management/LibraryManagement)
  - Contains `settings.py`, `urls.py`, `wsgi.py` and `asgi.py`. The `AUTH_USER_MODEL` points to the custom `accounts.LibraryUser` model.

- **Static / templates / media**: Paths: [library-management/static](library-management/static), [library-management/templates](library-management/templates), [library-management/media](library-management/media)
  - Static assets, shared templates (including chatbot partials), and uploaded media (book covers, profile images).

**Other services in this repository (not part of the Django project)**

- **recommendation_service/**
  - A separate process responsible for building and serving book embeddings and recommendation data (embedding generation, DB access).
  - Get the [service here](https://github.com/peterkahumu/library-recommendation-service)

- **library-chatbot-service/**
  - A standalone FastAPI service that provides the chatbot backend used by the frontend UI. 
  - Get the [service here](https://github.com/peterkahumu/library-chatbot-service)

**Notes & maintenance**

- Management commands live under individual apps (e.g., `books.management.commands`). Use `python manage.py help` to list available commands.
- Migrations are stored per-app in `migrations/` directories. Run `python manage.py migrate` after pulling schema changes.
- The frontend includes chatbot UI under `templates/components` and JS under `static/js` that call the separate chatbot service; the service runs independently from the Django app.


