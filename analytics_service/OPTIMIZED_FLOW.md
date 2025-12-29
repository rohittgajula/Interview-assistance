# Optimized Analytics Flow - Spark + Airflow

## 🎯 Final Architecture Design

Based on requirements:
- ✅ **Airflow**: Generate questions (scheduled, before session starts)
- ✅ **Spark**: Real-time answer processing during session
- ✅ **Spark**: Generate session report immediately after completion
- ✅ **Airflow**: Generate comprehensive analytics reports (on-demand or scheduled)

---

## 📊 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLOW 1: QUESTION GENERATION                       │
│                        (Airflow DAG)                                 │
└─────────────────────────────────────────────────────────────────────┘

Step 1: User creates practice session in frontend
        ↓
Step 2: interview_service creates PracticeSession in DB
        Status: 'scheduled'
        ↓
Step 3: interview_service publishes to Kafka
        Topic: practice-session.created
        Payload: {
          "session_id": "uuid",
          "job_role": {...},
          "num_questions": 5
        }
        ↓
Step 4: Kafka → Airflow Trigger
        - Kafka consumer in analytics_service
        - Triggers Airflow DAG: "generate_questions_dag"
        ↓
Step 5: Airflow DAG runs (Spark Submit)
        ├─ Task 1: Check Redis cache
        ├─ Task 2: Generate questions with OpenAI (if not cached)
        ├─ Task 3: Save to Redis cache
        └─ Task 4: Send to interview_service via Kafka
        ↓
Step 6: interview_service receives questions
        Topic: question.generated (x5)
        ↓
Step 7: interview_service saves to DB
        - Creates SessionQuestion records (x5)
        - Status: ready
        ↓
Step 8: Frontend displays "Questions Ready - Start Session"

⏱️ Time: 30 seconds (runs in background, async)
💾 Storage: PostgreSQL (interview_service DB)
🎯 Ready for session to start!


┌─────────────────────────────────────────────────────────────────────┐
│              FLOW 2: SESSION START & ANSWER PROCESSING               │
│                    (Spark Real-time Streaming)                       │
└─────────────────────────────────────────────────────────────────────┘

Step 1: User clicks "Start Session"
        Frontend → WebSocket → interview_service
        ↓
Step 2: interview_service updates session
        - PracticeSession.status = 'in_progress'
        - PracticeSession.started_at = now()
        - Sends question #1 via WebSocket
        ↓
Step 3: User answers question #1 (speaking/typing)
        ↓
Step 4: User clicks "Submit Answer"
        WebSocket → interview_service
        ↓
Step 5: interview_service saves answer to DB
        - SessionQuestion.answer_transcript = "..."
        - SessionQuestion.answered_at = now()
        ↓
Step 6: interview_service publishes to Kafka
        Topic: answer.submitted
        Payload: {
          "question_id": "uuid",
          "session_id": "uuid",
          "question_text": "...",
          "answer_transcript": "...",
          "expected_topics": [...]
        }
        ↓
Step 7: Spark Streaming Job receives event (runs 24/7)
        File: kafka_to_spark.py (Kafka-Spark Bridge)
        ↓
Step 8: Spark processes answer
        ├─ Check Redis cache (key: feedback:{question_id})
        ├─ If not cached:
        │   ├─ Call OpenAI API to analyze answer
        │   ├─ Calculate scores (technical, communication, etc.)
        │   └─ Cache in Redis (TTL: 2 hours)
        └─ Publish result to Kafka
        ↓
Step 9: Spark publishes feedback
        Topic: feedback.generated
        Payload: {
          "question_id": "uuid",
          "session_id": "uuid",
          "overall_score": 82.5,
          "technical_score": 85.0,
          "communication_score": 80.0,
          "feedback_text": "...",
          "strengths": [...],
          "improvements": [...]
        }
        ↓
Step 10: interview_service receives feedback
        ↓
Step 11: interview_service saves to DB
        - Creates QuestionFeedback record
        ↓
Step 12: interview_service sends to frontend
        WebSocket → User sees instant feedback
        ↓
Step 13: Frontend shows next question (repeat Steps 3-12 for Q2-Q5)

⏱️ Time per answer: 3-7 seconds
💾 Storage: PostgreSQL (QuestionFeedback) + Redis cache
🔄 Repeats for all questions


┌─────────────────────────────────────────────────────────────────────┐
│              FLOW 3: SESSION REPORT GENERATION                       │
│                    (Spark Real-time - Immediate)                     │
└─────────────────────────────────────────────────────────────────────┘

Step 1: User answers last question OR clicks "End Session"
        ↓
Step 2: interview_service marks session complete
        - PracticeSession.status = 'completed'
        - PracticeSession.ended_at = now()
        ↓
Step 3: interview_service publishes to Kafka
        Topic: session.completed
        Payload: {
          "session_id": "uuid",
          "user_id": "uuid",
          "num_questions": 5,
          "questions": [
            {"question_id": "q1", "feedback_id": "f1"},
            ...
          ]
        }
        ↓
Step 4: Spark Streaming Job receives event
        ↓
Step 5: Spark generates report (IMMEDIATELY)
        ├─ Fetch all feedback from Redis cache
        ├─ Aggregate scores using Spark transformations
        ├─ Calculate metrics:
        │   • Overall score (weighted average)
        │   • Technical/Communication/Behavioral/Mindset breakdowns
        │   • Speaking metrics (filler words, pace, etc.)
        │   • Trends (improvement from last session)
        ├─ Call OpenAI for summary (cached if exists)
        │   • 2-3 sentence summary
        │   • Key strengths (5 points)
        │   • Areas for improvement (5 points)
        │   • Recommendations (5 points)
        └─ Cache report in Redis (TTL: 24 hours)
        ↓
Step 6: Spark publishes report
        Topic: report.generated
        Payload: {
          "session_id": "uuid",
          "overall_score": 79.5,
          "technical_score": 81.5,
          "summary": "Strong technical knowledge...",
          "key_strengths": [...],
          "areas_for_improvement": [...],
          "recommendations": [...]
        }
        ↓
Step 7: interview_service receives report
        ↓
Step 8: interview_service saves to DB
        - Creates SessionReport record
        ↓
Step 9: interview_service sends to frontend
        WebSocket → User sees comprehensive report
        ↓
Step 10: User downloads PDF (optional)

⏱️ Time: 5-10 seconds
💾 Storage: PostgreSQL (SessionReport) + Redis cache
📊 User sees report immediately after session ends


┌─────────────────────────────────────────────────────────────────────┐
│         FLOW 4: COMPREHENSIVE ANALYTICS REPORTS (Optional)           │
│              (Airflow DAG - Scheduled or On-Demand)                  │
└─────────────────────────────────────────────────────────────────────┘

Option A: Scheduled (Automatic)
────────────────────────────────
Trigger: Every day at 2:00 AM (Airflow Scheduler)

Step 1: Airflow triggers DAG: "daily_analytics_dag"
        ↓
Step 2: Spark Job reads all sessions from last 24 hours
        - Read from PostgreSQL (via JDBC)
        - Or read from Kafka replay
        ↓
Step 3: Spark calculates analytics with SQL
        SELECT
          user_id,
          COUNT(*) as sessions_today,
          AVG(overall_score) as avg_score_today,
          SUM(duration_minutes) as practice_time_today,
          -- Calculate 7-day moving average
          -- Compare with previous day
          -- Identify trends
        FROM sessions
        WHERE date = CURRENT_DATE - 1
        GROUP BY user_id
        ↓
Step 4: Spark generates insights
        - Top performers
        - Users needing help
        - Popular job roles
        - Common improvement areas
        ↓
Step 5: Save results
        - Write to PostgreSQL (analytics tables)
        - Write to Redis (dashboard cache)
        - Generate PDF reports (MinIO/S3)
        ↓
Step 6: Send notifications (optional)
        - Email digest to users
        - Slack notification to admins

⏱️ Time: 2-5 minutes
📊 Frequency: Daily at 2 AM


Option B: On-Demand (Manual Trigger)
─────────────────────────────────────
Trigger: Admin clicks "Generate Analytics Report" in interview_service

Step 1: interview_service calls analytics_service API
        POST /api/analytics/generate-report
        {
          "report_type": "user_progress",
          "user_id": "uuid",
          "date_range": "last_30_days"
        }
        ↓
Step 2: analytics_service triggers Airflow DAG
        DAG: "on_demand_analytics_dag"
        Config: {user_id, date_range, report_type}
        ↓
Step 3: Airflow runs Spark Job
        - Read user's session data (30 days)
        - Calculate comprehensive metrics
        - Generate visualizations
        ↓
Step 4: Spark generates report
        - Progress trends (scores over time)
        - Skill breakdown
        - Filler word patterns
        - Speaking pace improvements
        - Comparison with peers
        ↓
Step 5: Save report
        - Generate PDF (MinIO/S3)
        - Save metadata to PostgreSQL
        ↓
Step 6: Return to interview_service
        Response: {
          "report_id": "uuid",
          "pdf_url": "https://minio.../reports/user-123.pdf",
          "status": "completed"
        }
        ↓
Step 7: interview_service shows download link to admin/user

⏱️ Time: 1-3 minutes
📊 Frequency: On-demand (when requested)
```

---

## 🎯 Key Design Decisions

### 1. Question Generation: **Airflow DAG** (Async, Before Session)
**Why?**
- ✅ Questions ready before user starts (no waiting)
- ✅ Can be cached and reused
- ✅ Doesn't block session start
- ✅ Airflow provides retry logic and monitoring

### 2. Answer Processing: **Spark Streaming** (Real-time)
**Why?**
- ✅ Instant feedback (3-7 seconds per answer)
- ✅ Streaming is perfect for event-by-event processing
- ✅ User doesn't wait at end of session
- ✅ Better UX (see feedback immediately)

### 3. Session Report: **Spark Streaming** (Real-time)
**Why?**
- ✅ Report ready immediately after session ends (5-10 sec)
- ✅ All data already in Redis from answer processing
- ✅ Fast aggregation with Spark
- ✅ No need to wait for batch job

### 4. Analytics Reports: **Airflow DAG** (Scheduled or On-Demand)
**Why?**
- ✅ Complex analytics don't need to be real-time
- ✅ Can process millions of records efficiently
- ✅ Scheduled for daily/weekly insights
- ✅ On-demand for specific user reports

---

## 📊 Data Flow Summary

```
┌────────────────────────────────────────────────────────────────┐
│                    DATA FLOW TIMELINE                          │
└────────────────────────────────────────────────────────────────┘

T=0s    User creates session
T=1s    Kafka: practice-session.created
T=2s    Airflow DAG triggered (runs in background)
T=30s   Questions ready in DB

        [User can start session anytime after questions are ready]

T=0s    User starts session, sees Q1
T=120s  User answers Q1
T=121s  Kafka: answer.submitted
T=122s  Spark receives event
T=126s  Spark publishes feedback (4 sec processing)
T=127s  User sees feedback for Q1
T=128s  User sees Q2

        [Repeat for Q2-Q5: ~10 minutes total]

T=600s  User answers Q5 (last question)
T=604s  User sees feedback for Q5
T=605s  Kafka: session.completed
T=606s  Spark receives event
T=610s  Spark generates report (4 sec aggregation)
T=611s  Spark publishes report
T=612s  User sees comprehensive report 🎉

        [Analytics runs in background]

T=2AM   Airflow: daily_analytics_dag runs
        Processes all sessions from yesterday
        Generates insights, trends, dashboards
```

---

## 💾 Storage Strategy

| Data | Where Stored | Why |
|------|--------------|-----|
| **Questions** | PostgreSQL (interview_service) | Permanent, queryable |
| **Questions (cache)** | Redis (2h TTL) | Fast retrieval, avoid re-generation |
| **Answers** | PostgreSQL (interview_service) | Permanent, user data |
| **Feedback** | PostgreSQL (interview_service) | Permanent, historical analysis |
| **Feedback (cache)** | Redis (2h TTL) | Fast aggregation for reports |
| **Session Reports** | PostgreSQL (interview_service) | Permanent, user views |
| **Reports (cache)** | Redis (24h TTL) | Fast retrieval |
| **Analytics Reports** | PostgreSQL + S3/MinIO | Historical analysis + PDFs |
| **Events Log** | Kafka (7 days retention) | Replay, audit, debugging |

---

## 🔄 Which Approach for Reports?

### **Recommendation: Hybrid Approach**

1. **Immediate Session Report** → **Spark Streaming** ✅
   - Generated right after session ends
   - Shows individual session performance
   - User sees it immediately (5-10 seconds)
   - Saved to `SessionReport` table

2. **Comprehensive Analytics** → **Airflow DAG** ✅
   - Daily/weekly/monthly trends
   - User progress over time
   - Comparison with other users
   - Advanced insights (ML predictions)
   - Generated on schedule OR on-demand

---

## 📝 Implementation Summary

### Kafka Topics

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `practice-session.created` | interview_service | analytics_service | Trigger question generation |
| `question.generated` | analytics_service (Airflow) | interview_service | Save questions to DB |
| `answer.submitted` | interview_service | analytics_service (Spark) | Real-time feedback |
| `feedback.generated` | analytics_service (Spark) | interview_service | Save feedback to DB |
| `session.completed` | interview_service | analytics_service (Spark) | Generate session report |
| `report.generated` | analytics_service (Spark) | interview_service | Save report to DB |

### Services Running 24/7

1. **Kafka-Spark Bridge** (kafka_to_spark.py)
   - Consumes: answer.submitted, session.completed
   - Processes: Real-time answer analysis & report generation
   - Publishes: feedback.generated, report.generated

2. **Airflow Scheduler**
   - Triggers DAGs on schedule or Kafka events
   - Monitors job execution
   - Provides UI for monitoring

### Airflow DAGs

1. **`generate_questions_dag`**
   - Trigger: Kafka event (practice-session.created)
   - Job: Generate questions with OpenAI
   - Output: Kafka (question.generated)

2. **`daily_analytics_dag`**
   - Trigger: Schedule (2 AM daily)
   - Job: Calculate user progress, trends
   - Output: PostgreSQL, Redis, PDF

3. **`on_demand_analytics_dag`**
   - Trigger: API call from interview_service
   - Job: Generate custom report for user/admin
   - Output: PDF to S3/MinIO

---

## ✅ Final Architecture Benefits

| Feature | Benefit |
|---------|---------|
| **Async Question Generation** | User doesn't wait, questions ready before session |
| **Real-time Feedback** | Instant scores after each answer (3-7 sec) |
| **Immediate Reports** | Session report ready 5-10 sec after completion |
| **Scheduled Analytics** | Daily insights without manual work |
| **On-Demand Reports** | Generate custom reports anytime |
| **Caching** | 80% cost reduction, 5x speed boost |
| **Scalable** | Spark cluster handles thousands of sessions |
| **Observable** | Airflow UI + Spark UI + logs |

---

## 🎯 Summary: Use This Flow!

1. ✅ **Create Session** → Airflow generates questions (async, 30 sec)
2. ✅ **Start Session** → User sees questions immediately
3. ✅ **Submit Answer** → Spark analyzes (real-time, 3-7 sec per answer)
4. ✅ **End Session** → Spark generates report (immediate, 5-10 sec)
5. ✅ **Daily Analytics** → Airflow runs batch job (2 AM, background)
6. ✅ **On-Demand Reports** → Airflow generates custom reports (API call)

**Perfect balance of real-time UX and efficient batch processing!** 🚀
