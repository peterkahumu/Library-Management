# Library Management System

> A role-based library platform built with Django 5.2 — manage inventory, automate borrowing workflows, surface analytics, and deliver AI-powered book recommendations and chatbot support.

[![Live Site](https://img.shields.io/badge/Live-library--management-blue?style=flat-square)](https://library-management-muf9.onrender.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white)](https://docs.djangoproject.com/en/5.2/)

---

## Table of Contents

- [Why This Project?](#why-this-project)
- [What It Does](#what-it-does)
- [Who Is This For?](#who-is-this-for)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [Full-Stack (Docker Compose)](#full-stack-docker-compose)
  - [Standalone (Django + DB + Redis)](#standalone-django--db--redis)
  - [Local Development (No Docker)](#local-development-no-docker)
- [Environment Variables](#environment-variables)
- [Database Requirements](#database-requirements)
- [Management Commands](#management-commands)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Dashboards](#dashboards)
- [External Services](#external-services)
- [Tech Stack](#tech-stack)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Additional Documentation](#additional-documentation)
- [License](#license)

---

## Why This Project?

Most library systems stop at check-in / check-out. This project goes further — it combines traditional library management with **behavioral analytics** and **AI-powered services** to create a smarter, more engaging experience for students, librarians, and administrators.

With this system you can:

- **Automate** the full borrowing lifecycle from request through return, with approval gates for librarians.
- **Discover** books through AI-powered personality-based recommendations and vector-similarity search.
- **Interact** with LibraBot, an embedded chatbot that answers library questions in real time.
- **Analyze** borrowing trends, peak usage hours, and genre popularity through role-specific dashboards.

---

## What It Does

- **Role-based access control** with custom user roles: `admin`, `librarian`, and `student`.
- **Book inventory management** supporting physical and digital formats.
- **Borrowing lifecycle support:**
  - Physical loans: `PENDING → ISSUED → RETURN_REQUESTED → RETURNED`
  - Digital loans: `DOWNLOADED`
- **Librarian workflows** for approving or rejecting borrow and return requests.
- **Admin, librarian, and student dashboards** with KPIs, logs, and borrowing analytics.
- **Google Books integration** — search, detail lookup, and import workflows (import restricted to admins and librarians).
- **Email notifications** for borrow and return events.
- **Redis-backed caching** with automatic signal-driven invalidation when books or genres change.
- **Security hardening** with CSP, HSTS, secure cookie flags, and clickjacking/MIME protections.
- **Personality-based recommendations** — the student dashboard calls the external [Recommendation Service](https://github.com/peterkahumu/library-recommendation-service) for personalized book suggestions powered by Big Five personality profiles.
- **Embedded LibraBot chatbot** — an in-app chat widget powered by the external [Chatbot Service](https://github.com/peterkahumu/library-chatbot-service) that streams AI responses via SSE.

---

## Who Is This For?

| Role | What You Get |
|------|-------------|
| **Students** | Browse the catalogue, borrow and return books, view personalized recommendations, and chat with LibraBot. |
| **Librarians** | Approve or reject borrow/return requests, track daily operations, and manage inventory. |
| **Administrators** | Full system oversight — analytics dashboards, user management, Google Books imports, and genre configuration. |
| **Developers** | A well-structured Django monolith with clean app boundaries, a comprehensive test suite, and microservice integration patterns. |

---

## Architecture Overview

This application is part of a multi-repository, microservice-oriented architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Root Repository                          │
│                                                             │
│  ┌───────────────────┐  ┌──────────────────┐  ┌──────────┐ │
│  │  library-management│  │ library-chatbot- │  │recommend-│ │
│  │  (Django App)      │  │ service (FastAPI)│  │ation_    │ │
│  │  :8000             │──│ :8001            │  │service   │ │
│  │                    │  │                  │  │(FastAPI) │ │
│  │                    │──┼──────────────────┘  │ :8002    │ │
│  │                    │  └─────────────────────│          │ │
│  └────────┬───────────┘                        └────┬─────┘ │
│           │                                         │       │
│  ┌────────▼───────────┐                    ┌────────▼─────┐ │
│  │  PostgreSQL + pgvec│◄───────────────────│  (shared DB) │ │
│  │  :5432             │                    └──────────────┘ │
│  └────────────────────┘                                     │
│  ┌────────────────────┐                                     │
│  │  Redis :6379       │                                     │
│  └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

- **This repository** (`library-management/`) is the Django web application.
- The [Chatbot Service](https://github.com/peterkahumu/library-chatbot-service) powers the LibraBot widget via SSE.
- The [Recommendation Service](https://github.com/peterkahumu/library-recommendation-service) provides personality-based and similarity-based book suggestions.
- All three services can be orchestrated together using the **root `docker-compose.yml`** in the parent directory.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required for local development |
| PostgreSQL | 12+ | With `pgvector` extension |
| Redis | 6+ | Optional locally; required for production parity |
| Docker & Docker Compose | Latest stable | Required for containerized setup |
| Git | Any recent | For cloning the repository |

---

## Quick Start

### Full-Stack (Docker Compose)

To run the **entire platform** — Django app, chatbot, recommendation engine, PostgreSQL, and Redis — you can orchestrate all services with a single `docker-compose.yml`. Each service lives in its own repository, so you will clone them side-by-side and create a root compose file.

1. **Create a project directory and clone all three repositories into it:**

   ```bash
   mkdir library-platform && cd library-platform

   git clone https://github.com/peterkahumu/Library-Management.git library-management
   git clone https://github.com/peterkahumu/library-chatbot-service.git library-chatbot-service
   git clone https://github.com/peterkahumu/library-recommendation-service.git recommendation_service
   ```

2. **Create the root `docker-compose.yml`** in `library-platform/` (the parent directory). Expand the block below and save the contents:

   <details>
   <summary><strong>Root <code>docker-compose.yml</code></strong> (click to expand)</summary>

   ```yaml
   services:
     app:
       build: ./library-management
       image: app
       command: bash -c "./wait-for-it.sh db:5432 -t 60 -- python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"
       volumes:
         - ./library-management:/app
       env_file:
         - ./library-management/.env
       depends_on:
         - db
         - redis
       ports:
         - "8000:8000"

     ai_service:
       build: ./library-chatbot-service
       image: ai_services
       volumes:
         - ./library-chatbot-service:/app
       ports:
         - "8001:8000"
       env_file:
         - ./library-chatbot-service/.env

     recommendation_service:
       build: ./recommendation_service
       image: recommendation_service
       volumes:
         - ./recommendation_service:/app
       ports:
         - "8002:8000"
       env_file:
         - ./library-management/.env
       depends_on:
         - db

     db:
       image: pgvector/pgvector:pg16
       volumes:
         - postgres_data:/var/lib/postgresql/data
       env_file:
         - ./library-management/.env
       environment:
         - POSTGRES_DB=${DB_NAME:-library_management}
         - POSTGRES_USER=${DB_USER:-library_management}
         - POSTGRES_PASSWORD=${DB_PASSWORD:-library_management}

     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"

   volumes:
     postgres_data:
   ```

   </details>

3. **Create the required `.env` files:**

   ```bash
   # Django app environment
   cp library-management/.env_example library-management/.env
   # Edit library-management/.env with your values (set DB_HOST=db and REDIS_URL=redis://redis:6379)

   # Chatbot service environment
   cp library-chatbot-service/.env_example library-chatbot-service/.env
   # Edit library-chatbot-service/.env — set OPENAI_API_KEY
   ```

4. **Start all services:**

   ```bash
   docker compose up --build
   ```

5. Open `http://localhost:8000` for the Django app.

This starts the following services:

| Service | Description | Internal Port | Host Port |
|---------|-------------|---------------|-----------|
| `app` | Django web application | 8000 | **8000** |
| `ai_service` | LibraBot chatbot (FastAPI) | 8000 | **8001** |
| `recommendation_service` | Book recommendations (FastAPI) | 8000 | **8002** |
| `db` | PostgreSQL with pgvector | 5432 | — |
| `redis` | Redis cache | 6379 | **6379** |

> **Note:** The services communicate over Docker's internal network. Ensure `DB_HOST=db` and `REDIS_URL=redis://redis:6379` in the Django `.env` file. The recommendation service shares the Django `.env` for database credentials.

### Standalone (Django + DB + Redis)

If you only need the Django application without the AI microservices, this repository includes its own `docker-compose.yml`:

```bash
cd library-management
cp .env_example .env
# Edit .env — set DB_HOST=db and REDIS_URL=redis://redis:6379
docker compose up --build
```

Open `http://localhost:8000`.

This starts `app` (Django), `db` (PostgreSQL), and `redis`. The LibraBot widget and recommendation sections will gracefully degrade when the external services are unavailable.

If you later want the chatbot or recommendations, run the [Chatbot Service](https://github.com/peterkahumu/library-chatbot-service) and [Recommendation Service](https://github.com/peterkahumu/library-recommendation-service) separately, then set `AI_SERVICE_URL` and `RECOMMENDATION_SERVICE_URL` in your `.env` file.

### Local Development (No Docker)

1. **Clone and set up a virtual environment:**

   ```bash
   git clone https://github.com/peterkahumu/Library-Management.git
   cd library-management
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # .venv\Scripts\activate    # Windows
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**

   ```bash
   cp .env_example .env
   # Edit .env with your local PostgreSQL and Redis connection details
   ```

3. **Prepare the database:**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Seed reference data (optional):**

   ```bash
   python manage.py seed_genres
   python manage.py seed_personality_data
   ```
   > The `seed_personality_data` command requires that you have some books in the database.

5. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

6. Visit `http://localhost:8000`.

---

## Environment Variables

Create a `.env` file from `.env_example` and configure the values for your deployment.

### Required

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key for cryptographic signing |
| `DEBUG` | Set to `True` for development, `False` for production |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL user |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | Database host (`localhost` locally, `db` in Docker) |
| `DB_PORT` | Database port (default: `5432`) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF |
| `REDIS_URL` | Redis connection URL (e.g., `redis://localhost:6379`) |

### Optional Integrations

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_BOOKS_API_KEY` | Enables Google Books search and import | — |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name for production media storage | — |
| `CLOUDINARY_API_KEY` | Cloudinary API key | — |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | — |
| `AI_SERVICE_URL` | [Chatbot Service](https://github.com/peterkahumu/library-chatbot-service) endpoint | `http://localhost:8001/` |
| `RECOMMENDATION_SERVICE_URL` | [Recommendation Service](https://github.com/peterkahumu/library-recommendation-service) endpoint | `http://localhost:8002/` |
| `DEFAULT_FROM_EMAIL` | Sender address for email notifications | — |

See `.env_example` for the full list of variable names.

---

## Database Requirements

The book model includes a 768-dimensional vector field for embeddings, so PostgreSQL must have the `pgvector` extension installed:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

If you use a managed database or a local PostgreSQL instance, verify the extension is available before running migrations. The Docker Compose setup uses `pgvector/pgvector:pg16`, which includes the extension out of the box.

---

## Management Commands

| Command | Description |
|---------|-------------|
| `python manage.py seed_genres` | Populate the genre table from `books.constants` |
| `python manage.py seed_personality_data` | Create synthetic users and personality-biased borrowing transactions |
| `python manage.py seed_superuser` | Seed an admin account from environment variables |
| `python manage.py clear_cache` | Clear the application cache and invalidate known cache keys |
| `python manage.py createsuperuser` | Django built-in — create an admin account interactively |

> **Note:** `seed_personality_data` requires books to already exist in your database. Run `seed_genres` first, then import or add books before seeding personality data.

---

## Testing

```bash
# Local
python manage.py test

# Docker
docker compose exec app python manage.py test
```

Tests automatically use **SQLite** and **LocMemCache** instead of PostgreSQL and Redis, so no external services are needed. The project includes **200+ tests** covering authentication, circulation workflows, dashboard analytics, caching, and form validation.

---

## Project Structure

```
library-management/
├── LibraryManagement/        # Django project settings and root URL config
├── accounts/                 # Custom user model, forms, signals, and auth flows
├── books/                    # Catalogue, inventory, Google Books, and embeddings
├── book_circulation/         # Borrow/return workflows and transaction logic
├── dashboards/               # Role-specific dashboards and analytics
├── pages/                    # Landing page and role-based entry points
├── caching/                  # Cache keys and cache services
├── communications/           # Email delivery service
├── docs/                     # Additional project documentation
├── templates/                # Django HTML templates
├── static/                   # CSS, JS, and image assets
├── tests/                    # Integration tests
├── docker-compose.yml        # Standalone compose (Django + DB + Redis)
├── Dockerfile                # Production-ready Docker image
├── requirements.txt          # Python dependencies
├── DEVELOPER.md              # Developer setup, security, testing, and troubleshooting
└── manage.py                 # Django CLI entry point
```

---

## Dashboards

The `dashboards` app exposes role-aware dashboards under `/dashboard/`:

| Route | Role | Highlights |
|-------|------|-----------|
| `/dashboard/admin/` | Admin | KPIs, borrowing trends, genre analytics, active-day/hour/user stats, recent activity |
| `/dashboard/librarian/` | Librarian | Daily operational metrics (issued, returned, overdue, pending), recent transactions |
| `/dashboard/student/` | Student | Personal borrowing summary, overdue/fine estimates, quick actions, AI recommendations |
| `/dashboard/logs/` | Admin | Paginated transaction logs with filters (date, status, user code, day of week, hour) |

---

## External Services

This application is designed to integrate with two companion microservices:

| Service | Repository | Purpose | Default URL |
|---------|-----------|---------|-------------|
| **LibraBot Chatbot** | [library-chatbot-service](https://github.com/peterkahumu/library-chatbot-service) | Streams AI chat responses via SSE to the embedded chat widget | `http://localhost:8001/` |
| **Recommendation Engine** | [library-recommendation-service](https://github.com/peterkahumu/library-recommendation-service) | Personality-based and similarity-based book recommendations | `http://localhost:8002/` |

Both services are **optional** — the Django application degrades gracefully when they are unavailable. Recommendation sections are omitted from the student dashboard, and the LibraBot widget shows an unavailable state.

### Integration Points

- **Chatbot widget:** `static/js/chatbot.js` + `templates/components/chatbot.html`
- **Recommendation hooks:** `dashboards/views.py` calls the recommendation service via `httpx`
- **CSP configuration:** `CSP_CONNECT_SRC` includes `http://localhost:8001` for local development

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2, Python 3.10+ |
| API Clients | `httpx`, `requests` |
| Database | PostgreSQL with `pgvector` extension |
| Cache | Redis via `django-redis` (LocMemCache in tests) |
| Media/Static | Cloudinary (production), WhiteNoise (static files) |
| Frontend | Django templates, Bootstrap 5, vanilla JavaScript |
| Containerization | Docker, Docker Compose |
| Code Quality | Black, Flake8, pre-commit hooks |
| Testing | Django TestCase (200+ tests, SQLite in CI) |

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Static files not loading | CSP blocking local resources | Run `python manage.py collectstatic --noinput` and check the browser console for CSP violations |
| Database connection errors | PostgreSQL not running or wrong credentials | Verify `DB_HOST`, `DB_USER`, `DB_PASSWORD` in `.env`; run `docker compose ps` to check containers |
| Redis connection errors | Redis not running | Run `redis-cli ping` (should return `PONG`) or check `docker compose ps` |
| LibraBot widget not responding | Chatbot service not running | Start the [Chatbot Service](https://github.com/peterkahumu/library-chatbot-service) and verify `AI_SERVICE_URL` in `.env` |
| Recommendations not showing | Recommendation service not running or no embeddings | Start the [Recommendation Service](https://github.com/peterkahumu/library-recommendation-service), run `embed_books.py`, and verify `RECOMMENDATION_SERVICE_URL` |
| `pgvector` errors during migration | Extension not installed | Run `CREATE EXTENSION IF NOT EXISTS vector;` in your PostgreSQL database |
| Docker build failures | Stale cache or volumes | Run `docker compose down -v && docker compose build --no-cache && docker compose up` |
| Test database cleanup issues | Connections still open | Run `docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS test_LibraryManagement;"` |

---

## Contributing

Contributions are welcome! To get started:

1. Fork this repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Install pre-commit hooks: `pre-commit install`.
4. Make your changes and verify they pass: `python manage.py test`.
5. Run code formatting: `black .` and `flake8`.
6. Submit a pull request with a clear description of your changes.

Please read `DEVELOPER.md` for detailed guidance on local setup, security configuration, and coding standards.

---

## Additional Documentation

| Document | Description |
|----------|-------------|
| [DEVELOPER.md](DEVELOPER.md) | Developer setup, Docker workflows, security configuration, testing, and troubleshooting |
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/APPS.md](docs/APPS.md) | App-by-app model, view, and URL overview |
| [docs/SECURITY.md](docs/SECURITY.md) | Security policy and vulnerability reporting |
| [Chatbot Service README](https://github.com/peterkahumu/library-chatbot-service) | LibraBot microservice documentation |
| [Recommendation Service README](https://github.com/peterkahumu/library-recommendation-service) | Recommendation microservice documentation |

---

## License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2026 Peter Muhumuki.
