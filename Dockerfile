# Use a slim Python base image
FROM python:3.12-slim

# Make Python behave well in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# System dependencies (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy Python requirements first to leverage Docker layer caching
COPY backend/requirements.txt ./requirements.txt

# Install deps and a production WSGI server
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy the whole repo (Flask app lives under /app/backend)
COPY . .

# Cloud Run injects $PORT at runtime. Bind gunicorn to it.
# The Flask "app" object is at backend/app.py -> app
CMD ["bash", "-lc", "exec gunicorn -w 2 -k gthread -b :${PORT:-8080} backend.app:app"]

