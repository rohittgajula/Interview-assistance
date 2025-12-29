"""
Utility to create and configure Spark sessions
"""
from pyspark.sql import SparkSession
import os


def create_spark_session(app_name="AnalyticsService"):
    """
    Create and configure Spark session with Kafka support

    Args:
        app_name: Application name for Spark UI

    Returns:
        SparkSession configured for analytics workloads
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .master(os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")) \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.apache.spark:spark-avro_2.12:3.5.0") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoint") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.default.parallelism", "4") \
        .config("spark.executor.memory", "2g") \
        .config("spark.executor.cores", "2") \
        .config("spark.driver.memory", "1g") \
        .config("spark.streaming.stopGracefullyOnShutdown", "true") \
        .getOrCreate()

    # Set log level
    spark.sparkContext.setLogLevel("WARN")

    return spark


def stop_spark_session(spark):
    """Stop Spark session gracefully"""
    if spark:
        spark.stop()
