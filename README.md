# Library Management System

Library Management System is a Django 5.2 application for running a library with role-based workflows for admins, librarians, and students.

The project includes a multi-app Django backend, Redis-backed caching with signal-driven invalidation, Google Books search/import support, book recommendation hooks, and an embedded LibraBot UI that connects to a separate FastAPI AI service.

## Live Site

`https://library-management-muf9.onrender.com/`

## What It Does

- Role-based access control with custom user roles: `admin`, `librarian`, and `student`
- Book inventory management with physical and digital formats
- Borrowing lifecycle support:
  - Physical loans: `PENDING -> ISSUED -> RETURN_REQUESTED -> RETURNED`
  - Digital loans: `DOWNLOADED`
- Librarian workflows for approving or rejecting borrow and return requests
- Admin, librarian, and student dashboards with KPIs, logs, and borrowing analytics
- Google Books search, detail lookup, and import workflows
- Email notifications for borrow and return events
- Redis-backed caching with automatic invalidation when books or genres change
- Security hardening with CSP, HSTS, secure cookie flags, and clickjacking/mime protections
- Personality profile support and recommendation-service hooks for personalized book suggestions
- Embedded LibraBot UI powered by the external AI microservice

## Dashboards App Highlights

The `dashboards` app exposes role-aware dashboards under `/dashboard/`:

- `admin/` - Admin KPIs, borrowing trends, genre analytics, active-day/hour/user stats, and recent activity
- `librarian/` - Daily operational metrics (issued, returned, overdue, pending borrow/return) plus recent transactions
- `student/` - Personal borrowing summary, overdue/fine estimates, quick actions, and recommendations
- `logs/` - Paginated transaction logs with filters (date, status, user code, day of week, hour)

### Recommendation Rendering (Student Dashboard)

Recommendation cards are rendered directly in the student dashboard template from context values set in `StudentDashboardView`.

- Personality recommendations call `POST {RECOMMENDATION_SERVICE_URL}recommend/personality` with `{ "user_id": "<uuid>" }`
- Similarity recommendations call `POST {RECOMMENDATION_SERVICE_URL}recommend/similar` with `{ "book_id": "<uuid>", "limit": 5 }`
- The template renders `personality_recommendations` and `similarity_recommendations` if present
- Personality cards display title, author, cover image, and a recommendation reason
- Similarity cards display title, author, and cover image, with a heading tied to the user's most recent borrowed book

If the recommendation service is unavailable or returns no results, the dashboard still loads and recommendation sections are omitted.

## Tech Stack

- Backend: Django 5.2
- API clients: `httpx`, `requests`
- Database: PostgreSQL, with SQLite used automatically for tests
- Cache: Redis via `django-redis`, with LocMemCache in tests
- Vector search: `pgvector`
- Media/Static: Cloudinary in production, WhiteNoise for static files
- Frontend: Django templates, Bootstrap 5, vanilla JavaScript
- Containerization: Docker and Docker Compose

## Quick Start

### Docker

This repository includes a standalone `docker-compose.yml` file for the Django app plus PostgreSQL and Redis.

```bash
git clone https://github.com/peterkahumu/Library-Management.git
cd library-management
cp .env_example .env
docker compose up --build
```

Open `http://localhost:8000`.

`docker compose up` starts:
- `app` (Django)
- `db` (PostgreSQL)
- `redis`

If you want the LibraBot widget or recommendation endpoints to respond locally, run the external AI and recommendation services separately and point `AI_SERVICE_URL` and `RECOMMENDATION_SERVICE_URL` at them.

### Local Development

Prerequisites:
- Python 3.10+
- PostgreSQL
- Redis (optional, but recommended for parity with production)

```bash
git clone https://github.com/peterkahumu/Library-Management.git
cd library-management
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env_example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Optional seed and maintenance commands:

```bash
python manage.py seed_genres
python manage.py seed_personality_data
python manage.py clear_cache
```

## Environment Variables

Create `.env` from `.env_example` and set the values that match your deployment.

### Required for normal operation

- `SECRET_KEY`
- `DEBUG`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `REDIS_URL`

### Optional integrations

- `GOOGLE_BOOKS_API_KEY` - Enables Google Books search/import support
- `CLOUDINARY_CLOUD_NAME` - Production media storage
- `CLOUDINARY_API_KEY` - Production media storage
- `CLOUDINARY_API_SECRET` - Production media storage
- `AI_SERVICE_URL` - LibraBot AI service endpoint, default `http://localhost:8001/`
- `RECOMMENDATION_SERVICE_URL` - Recommendation service endpoint, default `http://localhost:8002/`
- `DEFAULT_FROM_EMAIL` - Sender address used by the email service

See `.env_example` for the exact variable names and defaults.

## Database Requirements

The book model includes a 768-dimensional vector field for embeddings, so PostgreSQL needs the `pgvector` extension enabled.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

If you use a managed database or a local PostgreSQL instance, make sure the extension is available before running migrations.

## Management Commands

Custom commands currently available in this module:

- `python manage.py seed_genres` - Populate the genre table from `books.constants`
- `python manage.py seed_personality_data` - Create synthetic users and personality-biased borrowing transactions
- `python manage.py clear_cache` - Clear the application cache and invalidate known cache keys

For admin user creation, use Django's built-in `python manage.py createsuperuser`.

## Testing

```bash
python manage.py test
```

Or with Docker:

```bash
docker compose exec app python manage.py test
```

Tests automatically use SQLite and LocMemCache instead of PostgreSQL and Redis.

## Documentation

- `DEVELOPER.md` - setup, Docker, security, testing, and troubleshooting
- `docs/README.md` - documentation index
- `docs/APPS.md` - app-by-app model, view, and URL overview
- `docs/SECURITY.md` - security policy and reporting

## Project Structure

```text
library-management/
|-- LibraryManagement/     # Django project settings and root urls
|-- accounts/              # Custom user model, forms, signals, and auth flows
|-- books/                 # Catalog, inventory, Google Books, and embeddings
|-- book_circulation/      # Borrow/return workflows and transaction logic
|-- dashboards/            # Role-specific dashboards and analytics
|-- pages/                 # Landing page and role-based entry points
|-- caching/               # Cache keys and cache services
|-- communications/        # Email delivery service
|-- docs/                  # Additional project documentation
|-- templates/             # Django templates
|-- static/                 # Static assets
|-- tests/                  # Integration tests
`-- manage.py
```

## External Services

This project is designed to work with two external services:

- The AI service that powers LibraBot, documented in the separate AI service repository
- The recommendation service, which the student dashboard calls for personality-based and similarity-based suggestions
