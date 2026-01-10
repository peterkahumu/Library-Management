# Developer Documentation

This guide provides detailed technical information for developers working on the Library Management System.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Development](#docker-development)
- [Security Configuration](#security-configuration)
- [Testing](#testing)
- [Database Management](#database-management)
- [Code Quality](#code-quality)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python**: 3.10 or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 6 or higher (for caching)
- **Docker & Docker Compose**: Latest stable version (recommended)
- **Git**: For version control

## Local Development Setup

### 1. Clone and Virtual Environment

```bash
git clone https://github.com/peterkahumu/Library-Management.git
cd library_management

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/MacOS
# OR
.venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root (use `.env_example` as template):

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Database (PostgreSQL)
DB_NAME=library_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis Cache
REDIS_URL=redis://localhost:6379

# Google Books API
GOOGLE_BOOKS_API_KEY=your-google-books-api-key
```

**Security Note**: Never commit `.env` files to version control. The `.gitignore` is configured to exclude them.

### 4. Database Setup

Ensure PostgreSQL is running, then:

```bash
# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# (Optional) Load sample data
python manage.py seed_library_data
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to see the application.

---

## Docker Development

### Using Pre-built Image (Recommended)

Pull the latest image from GitHub Container Registry:

```bash
docker pull ghcr.io/peterkahumu/library-management:latest
```

**Available image versions:**
- `latest` - Most recent stable build

### Docker Compose Setup

1. **Update Environment Variables**

   For Docker, ensure your `.env` file has:
   ```env
   DB_HOST=db
   REDIS_URL=redis://redis:6379
   ```

2. **Build and Run**

   ```bash
   # Build services
   docker compose build

   # Start all services
   docker compose up

   # Or run in detached mode
   docker compose up -d
   ```

3. **Run Management Commands**

   ```bash
   # Run migrations
   docker compose exec app python manage.py migrate

   # Create superuser
   docker compose exec app python manage.py createsuperuser

   # Collect static files
   docker compose exec app python manage.py collectstatic --noinput

   # Load sample data
   docker compose exec app python manage.py seed_library_data
   ```

4. **View Logs**

   ```bash
   # All services
   docker compose logs -f

   # Specific service
   docker compose logs -f app
   ```

5. **Stop Services**

   ```bash
   docker compose down

   # Remove volumes (database data)
   docker compose down -v
   ```

---

## Security Configuration

The application implements comprehensive security measures to protect against common web vulnerabilities.

### Cookie Security

**Session and CSRF Cookies** are protected with security flags:

- **Production (DEBUG=False)**:
  - `SESSION_COOKIE_SECURE = True` - Cookies only sent over HTTPS
  - `SESSION_COOKIE_HTTPONLY = True` - JavaScript cannot access cookies
  - `CSRF_COOKIE_SECURE = True` - CSRF token only sent over HTTPS
  - `CSRF_COOKIE_HTTPONLY = True` - JavaScript cannot access CSRF token

- **Development (DEBUG=True)**:
  - `SESSION_COOKIE_HTTPONLY = True` - XSS protection maintained
  - `CSRF_COOKIE_HTTPONLY = True` - XSS protection maintained
  - `SESSION_COOKIE_SECURE = False` - Allow HTTP for local development
  - `CSRF_COOKIE_SECURE = False` - Allow HTTP for local development

### HTTP Strict Transport Security (HSTS)

**Production only** - Forces browsers to only use HTTPS:

```python
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Content Security Policy (CSP)

**Applied in both development and production** to prevent XSS attacks:

```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'", "https://cdn.jsdelivr.net")
```

**Note**: CSP is configured to allow Bootstrap and Font Awesome from CDNs. Adjust as needed for your deployment.

### Additional Security Headers

```python
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME sniffing
X_FRAME_OPTIONS = "DENY"  # Prevent clickjacking
```

### Security.txt

Vulnerability disclosure information is available at `/.well-known/security.txt`. Update the contact email in `static/.well-known/security.txt` before deployment.

---

## Testing

### Running Tests

**With Docker** (recommended):
```bash
docker compose exec app python manage.py test
```

**Without Docker**:
```bash
python manage.py test
```

### Test Coverage

The project has **214 tests** covering:
- User authentication and permissions
- Book circulation workflows
- Dashboard analytics
- Caching logic
- Form validation

### Writing Tests

Tests are located in `<app>/tests.py` files. Example:

```python
from django.test import TestCase
from accounts.models import LibraryUser

class UserModelTests(TestCase):
    def test_user_creation(self):
        user = LibraryUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.assertEqual(user.username, "testuser")
```

---

## Database Management

### Migrations

**Creating Migrations**:
```bash
# Docker
docker compose exec app python manage.py makemigrations

# Local
python manage.py makemigrations
```

**Applying Migrations**:
```bash
# Docker
docker compose exec app python manage.py migrate

# Local
python manage.py migrate
```

**Viewing Migration Status**:
```bash
python manage.py showmigrations
```

### Models Overview

For detailed information about application models, see:
- [Application Documentation](docs/APPS.md) - Complete models breakdown
- Individual model files:
  - `accounts/models.py` - User and authentication
  - `books/models.py` - Book inventory
  - `book_circulation/models.py` - Borrowing and returns
  - `dashboards/models.py` - Analytics

### Sample Data

Load sample books, users, and transactions:
```bash
docker compose exec app python manage.py seed_library_data
```

---

## Code Quality

### Code Formatting

The project uses **Black** for code formatting:

```bash
# Format all Python files
black .

# Check without modifying
black --check .
```

### Linting

**Flake8** checks code style:

```bash
flake8
```

Configuration is in `.flake8`:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git, __pycache__, .venv, migrations
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Configuration is in `.pre-commit-config.yaml`.

---

## Troubleshooting

### Common Issues

#### 1. **Static files not loading in development**

Ensure CSP allows local resources. Check browser console for CSP violations.

```bash
# Collect static files
python manage.py collectstatic --noinput
```

#### 2. **Database connection errors**

Check PostgreSQL is running:
```bash
# Check Docker container
docker compose ps

# View database logs
docker compose logs db
```

Verify `.env` database credentials match your PostgreSQL setup.

#### 3. **Redis connection errors**

Ensure Redis is running:
```bash
# Docker
docker compose ps

# Local
redis-cli ping  # Should return PONG
```

#### 4. **Test database cleanup issues**

If tests fail with "database is being accessed by other users":

```bash
# Manually drop test database
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS test_LibraryManagement;"
```

#### 5. **CSP blocking resources**

If Bootstrap styles aren't loading, check:
- Browser console for CSP violations
- `settings.py` CSP directives include necessary CDN domains
- Clear browser cache

#### 6. **Docker build failures**

```bash
# Clean rebuild
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Getting Help

- **Application Architecture**: See [docs/APPS.md](docs/APPS.md)
- **Security Policy**: See [docs/SECURITY.md](docs/SECURITY.md)
- **Issues**: Report bugs via GitHub Issues

---

## Project Structure

```
library_management/
├── LibraryManagement/      # Project settings and configuration
│   ├── settings.py         # Main settings file
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI entry point
├── accounts/              # User authentication
├── books/                 # Book inventory management
├── book_circulation/      # Borrowing/returning logic
├── dashboards/            # Analytics and KPIs
├── pages/                 # Static pages (home)
├── caching/               # Cache utilities
├── communications/        # Email notifications
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker orchestration
├── Dockerfile            # Docker image definition
└── manage.py             # Django CLI
```

---

## Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Bootstrap 5**: https://getbootstrap.com/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/documentation
- **Docker**: https://docs.docker.com/
