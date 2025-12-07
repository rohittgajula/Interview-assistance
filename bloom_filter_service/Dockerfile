

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create logs directory
RUN mkdir -p /app/logs && chmod 755 /app/logs

EXPOSE 8002

CMD [ "gunicorn", "bloom_filter_service.wsgi:application", "--bind", "0.0.0.0:8002" ]


