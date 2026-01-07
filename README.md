# Library Management System

**Live Site**: [https://library-management-muf9.onrender.com/](https://library-management-muf9.onrender.com/)

A modular, robust, and aesthetically pleasing Django-based Library Management System. Designed to streamline library operations for Admins, Librarians, and Students.

## 🚀 Key Features

- **Role-Based Access Control**:
    - **Admins**: Full system oversight, user role management, and analytics.
    - **Librarians**: Manage book circulation, approve/reject requests, and track inventory.
    - **Students**: Browse catalog, borrow books, and view personal transaction history.
- **Book Circulation**:
    - Complete workflow: Borrow Request -> Approval -> Issue -> Return Request -> Return Confirmation.
    - Support for **Hardcopy**, **E-books**, and **Audiobooks**.
- **Inventory Management**: Automated stock tracking (decrements on borrow, increments on return).
- **Dashboards**: Dedicated dashboards for each user role with relevant KPIs and charts.
- **Notifications**: Automated email notifications for overdue books and status updates.

## 🛠 Technology Stack

- **Backend**: [Django 5.2](https://www.djangoproject.com/) (Python)
- **Database**: PostgreSQL
- **Caching**: Redis
- **Frontend**: Bootstrap 5, Vanilla CSS
- **Containerization**: Docker & Docker Compose

## 📚 Documentation

Detailed documentation for the project's architecture and components can be found in the `docs/` directory:

- [**Application Documentation**](docs/APPS.md): In-depth look at Models, URLs, and Views for each app.

## 💻 Setup Instructions

### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis
- Git

### Local Development

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd library_management
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file in the root directory (use `.env_example` as a template):
    ```env
    SECRET_KEY=your_secret_key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=localhost
    DB_PORT=5432
    REDIS_URL=redis://localhost:6379
    ```

5.  **Run Migrations**:
    ```bash
    python manage.py migrate
    ```

6.  **Create Superuser**:
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the Server**:
    ```bash
    python manage.py runserver
    ```

### 🐳 Docker Setup

The application is fully containerized. To run using Docker:

1.  **Ensure Docker and Docker Compose are installed.**
2.  **Update `.env`**: Set `DB_HOST=db` and `REDIS_URL=redis://redis:6379` in your `.env` file.
3.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
    The application will be accessible at `http://localhost:8000`.

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
