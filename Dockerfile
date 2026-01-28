# Governance App - Docker
# Run: docker build -t governance-app . && docker run -p 8000:8000 governance-app

FROM python:3.11-slim

# Avoid buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code (excludes listed in .dockerignore)
COPY . .

# Port (Azure Container Apps / Cloud Run often set PORT)
ENV PORT=8000
EXPOSE 8000

# Run with Gunicorn (same as Azure Web App startup command)
CMD gunicorn --bind 0.0.0.0:${PORT} --timeout 600 --workers 2 wsgi:application
