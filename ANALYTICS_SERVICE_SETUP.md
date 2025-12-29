# Analytics Service - Integrated Setup Guide

## ✅ What Was Done

The analytics service (Apache Spark + Airflow) has been **successfully merged** into the root docker-compose.yml.

---

## 🔧 Changes Made

### 1. Fixed Port Conflict
- **kafka-ui**: Moved from port **8081** → **8084**
- **Airflow UI**: Now uses port **8081**

### 2. Added to Root docker-compose.yml

**New Services Added:**
- ✅ spark-master (Port 8082, 7077)
- ✅ spark-worker-1, spark-worker-2
- ✅ postgres-airflow, redis-analytics (Port 6380)
- ✅ airflow-init, airflow-webserver, airflow-scheduler
- ✅ kafka-spark-bridge (24/7 processing)

### 3. Network Integration
- All services use same backend network
- Kafka-Spark bridge → kafka:29092
- Spark/Airflow → redis-analytics:6379

---

## 📋 Port Summary

| Service | Port | URL |
|---------|------|-----|
| Nginx | 80 | http://localhost |
| Kafka UI | 8084 | http://localhost:8084 |
| Airflow UI | 8081 | http://localhost:8081 (admin/admin) |
| Spark UI | 8082 | http://localhost:8082 |
| Redis Analytics | 6380 | localhost:6380 |
| MinIO Console | 9001 | http://localhost:9001 |

---

## 🚀 Start Everything

```bash
# Single command
docker-compose up --build -d

# Watch logs
docker-compose logs -f
```

---

## 🔨 Next Steps

1. Create Spark job files from SPARK_JOBS_IMPLEMENTATION.md
2. Add OPENAI_API_KEY to .env
3. Test the flow

---

**Ready to process!** 🚀
