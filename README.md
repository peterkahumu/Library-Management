# Library Management System

Library Management System is a Django 5.2 application for running a library with role-based workflows for admins, librarians, and students.

The project includes:
- A multi-app Django backend (`accounts`, `books`, `book_circulation`, `dashboards`, `pages`)
- Redis-backed caching with signal-driven invalidation
- Google Books search/import support
- A separate [FastAPI AI microservice](https://github.com/peterkahumu/library-ai-service) used by the in-app LibraBot widget

## Live Site

`https://library-management-muf9.onrender.com/`

## Core Features

- Role-based access control with custom user roles (`admin`, `librarian`, `student`)
- Book inventory management with physical and digital formats
- Borrowing lifecycle:
  - Physical: `PENDING -> ISSUED -> RETURN_REQUESTED -> RETURNED`
  - Digital: `DOWNLOADED`
- Librarian workflows for approving/rejecting borrow and return requests
- Admin and librarian dashboard KPIs and transaction analytics
- Student dashboard with active loans, pending requests, and overdue/fine indicators
- Email notifications for circulation events
- Security hardening (CSP, HSTS, secure cookie flags, frame/mime protections)
- Embedded LibraBot UI connected to `ai_service` streaming endpoint

## Tech Stack

- Backend: Django 5.2
- AI Service: FastAPI + OpenAI-compatible client (ChatGPT)
- Database: PostgreSQL (SQLite automatically used for tests)
- Cache: Redis (`django-redis`), LocMemCache in tests
- Media/Static: Cloudinary (production media), WhiteNoise (static)
- Frontend: Django templates, Bootstrap 5, vanilla JavaScript
- Containerization: Docker and Docker Compose

## Quick Start

### Docker (recommended)

This repository includes a standalone `docker-compose.yml` file to run the library management app and its dependencies (PostgreSQL and Redis).

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

> [!NOTE]
> **AI Service Integration**
> The library management application integrates with a separate AI microservice to power the LibraBot widget.
> To run the complete stack including the chatbot, please clone the AI service repository:
> **[AI Service Repository](https://github.com/peterkahumu/library-ai-service.git)**

### Local development

Prerequisites:
- Python 3.10+
- PostgreSQL
- Redis (optional but recommended for parity)

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

Optional seed commands:

```bash
# populate the database with pre-defined genres.
python manage.py seed_genres
```

## Environment Variables

Create `.env` from `.env_example` and set at least:

- `SECRET_KEY`
- `DEBUG`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `ALLOWED_HOSTS`
- `REDIS_URL`
- `CSRF_TRUSTED_ORIGINS`

Optional integrations:
- `GOOGLE_BOOKS_API_KEY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `DEFAULT_FROM_EMAIL`

AI service variables are documented in `ai_service/README.md`.

## Management Commands

Available custom commands:
- `python manage.py seed_genres`
- `python manage.py clear_cache`

## Running Tests

```bash
python manage.py test
```

Or with Docker:

```bash
docker compose exec app python manage.py test
```

## Documentation

- `DEVELOPER.md`: setup, docker, security, testing, troubleshooting
- `docs/README.md`: documentation index
- `docs/APPS.md`: app-by-app model/view/url overview
- `docs/SECURITY.md`: security policy and reporting
- `ai_service/README.md`: AI microservice setup and API

## Project Structure

```text
library-management/
|-- LibraryManagement/     # Django project settings and root urls
|-- accounts/              # Custom user model and registration
|-- books/                 # Catalog, inventory, Google Books integration
|-- book_circulation/      # Borrow/return workflows and transaction logic
|-- dashboards/            # Role-specific dashboards and logs
|-- pages/                 # Landing and role-based redirect entrypoints
|-- caching/               # Cache keys/services and tests
|-- communications/        # Email delivery service
|-- ai_service/            # FastAPI chatbot service
|-- docs/                  # Additional project documentation
|-- templates/
|-- static/
|-- tests/
`-- manage.py
```
