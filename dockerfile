FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code (src/, templates/, database/)
COPY . .

# Flask needs to know where the app entrypoint is
# This points to the Flask instance "app" inside src/trivia_web.py
ENV FLASK_APP=src/trivia_web.py

# Your SQLite DB path inside container
ENV TRIVIA_DB_PATH=/app/database/database.db

EXPOSE 8001

# MATCH YOUR EXISTING PATTERN EXACTLY:
# Use Flask dev server listening on all interfaces
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8001"]
