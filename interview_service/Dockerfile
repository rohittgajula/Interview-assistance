FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# install required system packages (PostgreSQL client, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    ffmpeg \
    libmagic1 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7 && \
    rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt


COPY . .

EXPOSE 8001

RUN adduser --disabled-password django
USER django


CMD ["gunicorn", "auth_service.wsgi:application", "--bind", "0.0.0.0:8001"]