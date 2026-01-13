# Library Management System

**Live Site**: [https://library-management-muf9.onrender.com/](https://library-management-muf9.onrender.com/)

A modular, robust, and aesthetically pleasing Django-based Library Management System. Designed to streamline library operations for Admins, Librarians, and Students.

## 🚀 Key Features

- **Role-Based Access Control**:
    - **Admins**: Full system oversight, user role management, and analytics.
    - **Librarians**: Manage book circulation, approve/reject requests, and track inventory.
    - **Students**: Browse catalogue, borrow books, and view personal transaction history.
- **Book Circulation**:
    - Complete workflow: Borrow Request -> Approval -> Issue -> Return Request -> Return Confirmation.
    - Support for **Hardcopy**, **E-books**, and **Audiobooks**.
- **Inventory Management**: Automated stock tracking (decrements on borrow, increments on return).
- **Dashboards**: Dedicated dashboards for each user role with relevant KPIs and charts.
- **Google Books Integration**:
    -   **Search**: Integrated search with Google Books API to explore external book databases.
    -   **Seamless Import**: Admins and Librarians can instantly import book details into the local system.
    -   **Smart Duplication Check**: Automatically detects if a book already exists in the library.
- **Notifications**: Automated email notifications for overdue books and status updates.
- **🔒 Security**: Enterprise-grade security with HSTS, CSP, secure cookies, and more. See [DEVELOPER.md#security-configuration](DEVELOPER.md#security-configuration) for details.

## 🛠 Technology Stack

- **Backend**: [Django 5.2](https://www.djangoproject.com/) (Python)
- **Database**: PostgreSQL
- **Caching**: Redis
- **Frontend**: Bootstrap 5, Vanilla CSS
- **Containerization**: Docker & Docker Compose

## 📚 Documentation

Comprehensive documentation is available:

- [**DEVELOPER.md**](DEVELOPER.md): Complete developer guide including setup, Docker, security configuration, and troubleshooting
- [**Application Documentation**](docs/APPS.md): Detailed breakdown of Models, URLs, and Views for each app
- [**Security Policy**](docs/SECURITY.md): Vulnerability reporting and security features

## 💻 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/peterkahumu/Library-Management.git
cd library_management
cp .env_example .env  # Configure your environment variables
docker compose up --build
```

Visit `http://localhost:8000`

### Option 2: Local Development

```bash
git clone https://github.com/peterkahumu/Library-Management.git
cd library_management
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env_example .env  # Configure your environment variables
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**📖 For detailed setup, configuration, testing, and troubleshooting, see [DEVELOPER.md](DEVELOPER.md)**

## 🚀 Deployment

The application is ready for deployment on platforms like Render, Railway, or AWS.

### Deploying via Docker Image (GHCR)

You can build and push the Docker image to GitHub Container Registry (GHCR) for easy deployment.

1.  **Login to GHCR**:
    ```bash
    echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
    ```
2.  **Build the Image**:
    ```bash
    docker build -t ghcr.io/<username>/library-management:latest .
    ```
3.  **Push to Registry**:
    ```bash
    docker push ghcr.io/<username>/library-management:latest
    ```
4.  **Deploy**: Use the image URL `ghcr.io/<username>/library-management:latest` on your hosting provider (e.g., Render).

## 📂 Project Structure

```
library_management/
├── LibraryManagement/  # Project configuration (settings, main urls)
├── accounts/           # User authentication and custom models
├── books/              # Book inventory and management
├── book_circulation/   # Borrowing and returning logic
├── dashboards/         # Role-specific analytics and views
├── pages/              # Static pages (Home)
├── templates/          # HTML templates
├── static/             # CSS, JS, and Images
├── docs/               # Detailed documentation
└── manage.py           # Django management script
```
