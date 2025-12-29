FROM bitnami/spark:3.5

USER root

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy Spark applications
COPY spark /opt/spark-apps/spark
COPY kafka_integration /opt/spark-apps/kafka_integration
COPY config /opt/spark-apps/config

# Set working directory
WORKDIR /opt/spark-apps

USER 1001
