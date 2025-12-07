
# STAGE - 1
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# STAGE - 2
# install required system packages (PostgreSQL client, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    libmagic1 && \
    rm -rf /var/lib/apt/lists/*


# STAGE - 3
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# STAGE - 4
# copy project files
COPY . .

# Create logs directory
RUN mkdir -p /app/logs && chmod 755 /app/logs

# expose django port
EXPOSE 8000

# create a non-root use
RUN adduser --disabled-password django && \
    chown -R django:django /app/logs
USER django

# use gunicorn to run service
CMD ["gunicorn", "auth_service.wsgi:application", "--bind", "0.0.0.0:8000"]
# CMD ["gunicorn", "auth_service.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
