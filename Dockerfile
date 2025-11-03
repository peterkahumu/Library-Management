FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y\
    build-essential\
    libpq-dev\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x ./wait-for-it.sh

COPY . .
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver"]
