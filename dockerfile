# Use official Python
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (SQLite + compiler tools)
RUN apt-get update && apt-get install -y \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps with uv
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

# Copy your Django project code
COPY src/ /app/

# Expose port 8000 for Django/Gunicorn
EXPOSE 8000

# Start Gunicorn (production-ready server)
CMD ["gunicorn", "trivia_site.wsgi:application", "--bind", "0.0.0.0:8000"]
