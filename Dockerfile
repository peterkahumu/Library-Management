# Production ready Dockerfile
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

COPY --chown=appuser:appuser . .
RUN chmod +x ./wait-for-it.sh

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py clear_cache && gunicorn --bind 0.0.0.0:8000 LibraryManagement.wsgi:application"]