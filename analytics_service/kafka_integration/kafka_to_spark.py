"""
Kafka to Spark Bridge - Runs 24/7 as Spark Streaming Job

This is the main entry point that:
1. Reads from Kafka topics in real-time
2. Routes events to appropriate Spark processing jobs
3. Maintains streaming state
"""
import os
import sys
sys.path.append('/opt/spark-apps')

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_json, struct, lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, ArrayType
from spark.utils.spark_session import create_spark_session
from spark.jobs.question_generation_job import QuestionGenerationJob
from spark.jobs.feedback_analysis_job import FeedbackAnalysisJob
from spark.jobs.report_generation_job import ReportGenerationJob


# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Topics to consume
TOPICS = "practice-session.created,answer.submitted,session.completed"


def main():
    """
    Main streaming application that routes Kafka events to Spark jobs
    """
    print("=" * 70)
    print("🚀 Starting Kafka-Spark Bridge (Real-time Event Processing)")
    print("=" * 70)

    # Create Spark session
    spark = create_spark_session("KafkaSparkBridge")

    # Read from Kafka as stream
    kafka_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", TOPICS) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()

    print(f"✓ Connected to Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"✓ Subscribed to topics: {TOPICS}")
    print("✓ Streaming started - waiting for events...")
    print("=" * 70)

    # Parse Kafka messages
    # Each message has: key, value, topic, partition, offset, timestamp
    parsed_stream = kafka_stream.selectExpr(
        "CAST(key AS STRING) as key",
        "CAST(value AS STRING) as value",
        "topic",
        "partition",
        "offset",
        "timestamp"
    )

    # Process each batch of messages
    def process_batch(batch_df, batch_id):
        """
        Process each micro-batch of Kafka messages

        Args:
            batch_df: DataFrame containing messages from this batch
            batch_id: Unique identifier for this batch
        """
        if batch_df.isEmpty():
            return

        print(f"\n📦 Processing batch #{batch_id} ({batch_df.count()} events)")

        # Route based on topic
        for row in batch_df.collect():
            topic = row['topic']
            value = row['value']

            try:
                if topic == "practice-session.created":
                    print(f"  ├─ 🎯 Session Created: {row['key']}")
                    QuestionGenerationJob().process_event(value)

                elif topic == "answer.submitted":
                    print(f"  ├─ 💬 Answer Submitted: {row['key']}")
                    FeedbackAnalysisJob().process_event(value)

                elif topic == "session.completed":
                    print(f"  ├─ ✅ Session Completed: {row['key']}")
                    ReportGenerationJob().process_event(value)

                else:
                    print(f"  ├─ ⚠️  Unknown topic: {topic}")

            except Exception as e:
                print(f"  └─ ❌ Error processing {topic}: {e}")

        print(f"✓ Batch #{batch_id} completed\n")

    # Start streaming query with foreachBatch
    query = parsed_stream \
        .writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "/tmp/spark-checkpoint/kafka-bridge") \
        .start()

    print("🔥 Kafka-Spark Bridge is running!")
    print("📊 Monitoring Kafka topics for events...")
    print("Press Ctrl+C to stop\n")

    # Wait for termination
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping Kafka-Spark Bridge...")
        query.stop()
        spark.stop()
        print("✓ Stopped gracefully")


if __name__ == "__main__":
    main()
