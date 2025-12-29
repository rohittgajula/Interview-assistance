# Analytics Service - Complete Flow Explanation

## 🎯 How Everything Works Together

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTERVIEW SERVICE                               │
│  • User creates practice session                                       │
│  • User submits answers                                                │
│  • Session completes                                                   │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ Publishes Events to Kafka
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            KAFKA TOPICS                                 │
│  📨 practice-session.created                                            │
│  📨 answer.submitted                                                    │
│  📨 session.completed                                                   │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ Consumed By
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      KAFKA-SPARK BRIDGE                                 │
│  • Runs 24/7 as Spark Streaming Job                                    │
│  • Reads from Kafka in real-time                                       │
│  • Routes events to appropriate Spark jobs                             │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ Triggers Processing
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       APACHE SPARK CLUSTER                              │
│  ┌───────────────────────────────────────────────────────────┐         │
│  │  Spark Master (orchestrates)                              │         │
│  │    ├── Spark Worker 1 (2 cores, 2GB RAM)                 │         │
│  │    └── Spark Worker 2 (2 cores, 2GB RAM)                 │         │
│  └───────────────────────────────────────────────────────────┘         │
│                                                                          │
│  🔥 Real-time Jobs (Spark Streaming):                                   │
│     • Question Generation Job                                           │
│     • Feedback Analysis Job                                            │
│     • Report Generation Job                                            │
│                                                                          │
│  📊 Batch Jobs (scheduled by Airflow):                                  │
│     • Daily Analytics Report                                           │
│     • Weekly Trend Analysis                                            │
│     • ML Model Training                                                │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ Uses for AI Processing
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI PROVIDERS                                    │
│  • OpenAI GPT-4 (question generation, feedback)                        │
│  • Anthropic Claude (alternative)                                      │
│  • Custom ML Models (trained with Spark MLlib)                         │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ Caches Results In
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           REDIS CACHE                                   │
│  • Questions (TTL: 2 hours)                                            │
│  • Feedback (TTL: 2 hours)                                             │
│  • Reports (TTL: 24 hours)                                             │
│  • Analytics (TTL: 1 hour)                                             │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ Results Published To
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            KAFKA TOPICS                                 │
│  📤 question.generated                                                  │
│  📤 feedback.generated                                                  │
│  📤 report.generated                                                    │
└────────────────┬────────────────────────────────────────────────────────┘
                 │
                 │ Consumed By
                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTERVIEW SERVICE                               │
│  • Saves questions to database                                         │
│  • Saves feedback to database                                          │
│  • Sends results to WebSocket clients                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        APACHE AIRFLOW                                   │
│  • Schedules Spark jobs (hourly, daily, weekly)                        │
│  • Generates analytics reports                                         │
│  • Monitors job execution                                              │
│  • Sends alerts on failures                                            │
│  UI: http://localhost:8081                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Flow: Session Creation to Report

### **Flow 1: Question Generation** ⚡ Real-time

```
Step 1: User creates practice session in frontend
        ↓
Step 2: interview_service creates PracticeSession in database
        ↓
Step 3: interview_service publishes to Kafka
        Topic: practice-session.created
        Payload: {
          "session_id": "uuid",
          "user_id": "uuid",
          "job_role": {
            "title": "Senior Backend Developer",
            "required_skills": ["Python", "Django", "PostgreSQL"],
            "difficulty_level": "hard",
            "technical_weight": 0.5,
            "behavioral_weight": 0.3,
            "num_questions": 5
          }
        }
        ↓
Step 4: Kafka-Spark Bridge (Spark Streaming) receives event
        File: kafka_integration/kafka_to_spark.py
        - Reads from Kafka in real-time (runs 24/7)
        - Parses JSON payload
        - Routes to Question Generation Job
        ↓
Step 5: Spark Question Generation Job executes
        File: spark/jobs/question_generation_job.py

        5a. Check Redis cache for existing questions
            Key: "questions:{session_id}"

        5b. If NOT cached:
            - Extract job_role details from payload
            - Call OpenAI API to generate questions
            - Prompt: "Generate 5 questions for Senior Backend Developer
                      focusing on Python, Django, PostgreSQL
                      with 50% technical, 30% behavioral..."

        5c. OpenAI returns:
            [
              {
                "question_text": "Explain how Django ORM handles relationships",
                "category": "technical",
                "expected_topics": ["ORM", "relationships", "queries"]
              },
              ...
            ]

        5d. Cache in Redis (TTL: 2 hours)

        5e. For each question, publish to Kafka
            Topic: question.generated
            Payload: {
              "session_id": "uuid",
              "question_number": 1,
              "question_text": "...",
              "question_category": "technical",
              "expected_topics": [...]
            }
        ↓
Step 6: interview_service consumes from question.generated
        - Creates SessionQuestion in database
        - Sends to WebSocket → Frontend displays question
        ↓
Step 7: User sees question and starts recording answer

⏱️ Time: 2-5 seconds (with caching: <500ms)
💰 Cost: $0.02 per session (OpenAI API call)
```

---

### **Flow 2: Answer Feedback** ⚡ Real-time

```
Step 1: User finishes answering and clicks "Submit"
        Frontend sends answer via WebSocket
        ↓
Step 2: interview_service receives answer
        - Saves answer transcript to SessionQuestion
        - Marks answered_at timestamp
        ↓
Step 3: interview_service publishes to Kafka
        Topic: answer.submitted
        Payload: {
          "question_id": "uuid",
          "session_id": "uuid",
          "question_number": 1,
          "question_text": "Explain how Django ORM handles relationships",
          "answer_transcript": "Django ORM uses ForeignKey and ManyToMany...",
          "expected_topics": ["ORM", "relationships", "queries"],
          "job_role": {...}
        }
        ↓
Step 4: Kafka-Spark Bridge receives event
        - Routes to Feedback Analysis Job
        ↓
Step 5: Spark Feedback Analysis Job executes
        File: spark/jobs/feedback_analysis_job.py

        5a. Check Redis cache
            Key: "feedback:{question_id}"

        5b. If NOT cached:
            - Extract question and answer
            - Call OpenAI API to analyze
            - Prompt: "Analyze this interview answer:
                      Question: ...
                      Answer: ...
                      Expected topics: ...

                      Rate on:
                      - Technical: relevance, completeness, accuracy
                      - Communication: fluency, grammar, vocabulary
                      - Behavioral: confidence, professionalism
                      - Mindset: structure, critical thinking"

        5c. OpenAI returns:
            {
              "technical_score": 85,
              "communication_score": 78,
              "behavioral_score": 82,
              "mindset_score": 80,
              "overall_score": 81.5,
              "feedback_text": "Good understanding of ORM concepts...",
              "strengths": ["Clear explanation", "Good examples"],
              "improvements": ["Could mention lazy loading"]
            }

        5d. Cache in Redis (TTL: 2 hours)

        5e. Publish to Kafka
            Topic: feedback.generated
            Payload: {
              "question_id": "uuid",
              "session_id": "uuid",
              "overall_score": 81.5,
              "technical_score": 85,
              ...
            }
        ↓
Step 6: interview_service consumes from feedback.generated
        - Creates QuestionFeedback in database
        - Sends to WebSocket → Frontend displays feedback
        ↓
Step 7: User sees instant feedback with scores

⏱️ Time: 3-7 seconds per answer
💰 Cost: $0.03-0.05 per answer
📊 If 5 questions: ~15-35 seconds total, $0.15-0.25
```

---

### **Flow 3: Session Report** ⚡ Real-time

```
Step 1: User answers all questions OR clicks "End Session"
        ↓
Step 2: interview_service marks session as completed
        - Updates PracticeSession.status = 'completed'
        - Sets ended_at timestamp
        ↓
Step 3: interview_service publishes to Kafka
        Topic: session.completed
        Payload: {
          "session_id": "uuid",
          "user_id": "uuid",
          "num_questions": 5,
          "questions": [
            {"question_id": "q1", "feedback_id": "f1"},
            {"question_id": "q2", "feedback_id": "f2"},
            ...
          ]
        }
        ↓
Step 4: Kafka-Spark Bridge receives event
        - Routes to Report Generation Job
        ↓
Step 5: Spark Report Generation Job executes
        File: spark/jobs/report_generation_job.py

        5a. Check Redis cache
            Key: "report:{session_id}"

        5b. If NOT cached:
            - Fetch all feedback from Redis
            - Aggregate scores using Spark transformations

        5c. Calculate metrics:
            • Overall score (weighted average)
            • Technical breakdown (relevance, completeness, etc.)
            • Communication breakdown (fluency, grammar, etc.)
            • Speaking metrics (filler words, pace, etc.)
            • Trends (improvement from last session)

        5d. Call OpenAI for summary:
            - Prompt: "Analyze this interview session:
                      Overall: 79.5/100
                      Technical: 81.5/100
                      Communication: 76.8/100

                      Question performance:
                      Q1: 81.5 - Good understanding of ORM
                      Q2: 78.0 - Needs more depth on APIs
                      ...

                      Generate:
                      - 2-3 sentence summary
                      - 5 key strengths
                      - 5 areas for improvement
                      - 5 recommendations"

        5e. OpenAI returns comprehensive summary

        5f. Cache report (TTL: 24 hours)

        5g. Publish to Kafka
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
Step 6: interview_service consumes from report.generated
        - Creates SessionReport in database
        - Sends to WebSocket → Frontend shows report
        ↓
Step 7: User sees comprehensive session report

⏱️ Time: 5-10 seconds
💰 Cost: $0.03-0.05
📊 Total session cost: $0.20-0.35 (questions + feedback + report)
```

---

## ⏰ Scheduled Analytics Jobs (Airflow)

### **Flow 4: Daily User Analytics** 📊 Batch (Scheduled)

```
Time: Every day at 2:00 AM
Triggered by: Airflow DAG scheduler

Step 1: Airflow triggers Spark job at 2:00 AM
        DAG: daily_analytics_dag.py
        ↓
Step 2: Spark reads all sessions from yesterday
        File: spark/analytics/user_analytics.py

        - Query Kafka topics for all events from last 24 hours
        - Or read from parquet files in S3/MinIO
        ↓
Step 3: Calculate daily metrics with Spark SQL:

        SELECT
          user_id,
          COUNT(*) as sessions_today,
          AVG(overall_score) as avg_score_today,
          SUM(duration_minutes) as practice_time_today,
          MAX(overall_score) as best_score_today
        FROM sessions
        WHERE date = CURRENT_DATE - 1
        GROUP BY user_id
        ↓
Step 4: Calculate trends:
        - Compare with previous day
        - Calculate 7-day moving average
        - Identify improving/declining users
        ↓
Step 5: Store results:
        - Write to Redis (for quick dashboard access)
        - Write to S3/MinIO (for historical analysis)
        - Publish summary to Kafka (optional)
        ↓
Step 6: Generate PDF report (optional)
        - Top performers
        - Users needing help
        - Overall platform metrics
        ↓
Step 7: Send notifications (optional)
        - Email digest to users
        - Slack notification to admins

⏱️ Time: 2-5 minutes for 1000s of sessions
📊 Processes: All sessions from yesterday in one batch
```

---

### **Flow 5: Weekly Trend Analysis** 📈 Batch (Scheduled)

```
Time: Every Sunday at 3:00 AM
Triggered by: Airflow DAG scheduler

Step 1: Airflow triggers Spark job
        DAG: weekly_trends_dag.py
        ↓
Step 2: Spark reads all sessions from last 7 days
        File: spark/analytics/trend_analysis.py
        ↓
Step 3: Calculate trends with Spark:

        • Score progression by user
        • Popular job roles
        • Most challenging questions
        • Common improvement areas
        • Filler word patterns
        • Speaking pace improvements
        ↓
Step 4: Generate visualizations:
        - Score trend graphs
        - Skill distribution heatmaps
        - Improvement velocity charts
        ↓
Step 5: ML insights (optional):
        - Predict user success rate
        - Recommend personalized practice areas
        - Identify at-risk users
        ↓
Step 6: Save reports:
        - Write to S3/MinIO
        - Update Redis dashboard cache
        ↓
Step 7: Distribute reports:
        - Email weekly digest
        - Update admin dashboard

⏱️ Time: 5-10 minutes for large datasets
📊 Processes: Millions of records efficiently
```

---

### **Flow 6: ML Model Training** 🤖 Batch (Scheduled)

```
Time: Every month on 1st at 1:00 AM
Triggered by: Airflow DAG scheduler

Step 1: Airflow triggers Spark ML training job
        DAG: ml_training_dag.py
        ↓
Step 2: Load historical data with Spark
        File: spark/ml/training/train_scoring_model.py

        - Load all answered questions (100K+)
        - Load corresponding feedback scores
        ↓
Step 3: Prepare training data:

        Features:
        • Answer length (word count)
        • Technical keywords present
        • Sentence structure complexity
        • Filler word count
        • Speaking pace
        • Question category
        • Job role difficulty

        Target:
        • Overall score (0-100)
        ↓
Step 4: Train ML model with Spark MLlib:

        from pyspark.ml.regression import RandomForestRegressor
        from pyspark.ml.feature import VectorAssembler

        assembler = VectorAssembler(inputCols=features)
        rf = RandomForestRegressor(numTrees=100)
        model = rf.fit(training_data)
        ↓
Step 5: Evaluate model:
        - RMSE on test set
        - Feature importance
        - Prediction vs actual scatter plot
        ↓
Step 6: Save model:
        - Save to S3/MinIO
        - Version with timestamp
        - Update production model pointer
        ↓
Step 7: Deploy model:
        - Feedback job now uses ML model first
        - Only calls OpenAI for edge cases
        - 10x faster, 80% cost reduction!

⏱️ Time: 30-60 minutes for training
💰 Cost: Reduces per-answer cost from $0.05 to $0.01
🚀 Speed: Feedback in 500ms instead of 5 seconds
```

---

## 🔥 Real-time Streaming vs Batch Processing

### **Spark Streaming (Real-time)** ⚡
- **Runs**: 24/7 continuously
- **Processes**: Events as they arrive from Kafka
- **Latency**: 2-10 seconds
- **Use Cases**:
  - Question generation
  - Feedback analysis
  - Report generation
  - Live dashboards

### **Spark Batch (Scheduled)** 📊
- **Runs**: On schedule (hourly, daily, weekly)
- **Processes**: Large historical datasets
- **Latency**: Minutes to hours
- **Use Cases**:
  - Daily analytics reports
  - Trend analysis
  - ML model training
  - Data quality checks

---

## 💾 Data Storage Strategy

### **Redis (Cache)** - Fast temporary storage
```
✅ Use for:
• AI responses (questions, feedback)
• Real-time dashboard metrics
• Session state during practice
• ML model predictions

⏱️ TTL:
• Questions: 2 hours
• Feedback: 2 hours
• Reports: 24 hours
• Analytics: 1 hour
```

### **Kafka (Event Stream)** - Message queue
```
✅ Use for:
• Event-driven communication
• Replay-able event log
• Cross-service messaging
• Audit trail

⏱️ Retention:
• 7 days (configurable)
```

### **PostgreSQL (interview_service)** - Permanent storage
```
✅ Use for:
• User accounts
• Session records
• Questions & feedback (final)
• Reports (final)

⏱️ Retention:
• Forever (with backups)
```

### **S3/MinIO (Optional)** - Long-term storage
```
✅ Use for:
• Audio recordings
• Generated reports (PDF)
• ML training data
• Historical analytics

⏱️ Retention:
• Years (cheap storage)
```

---

## 🎯 Key Performance Metrics

| Metric | Real-time (Streaming) | Batch (Scheduled) |
|--------|----------------------|-------------------|
| **Latency** | 2-10 seconds | Minutes to hours |
| **Throughput** | 100s events/second | Millions of records |
| **Cost per operation** | $0.02-0.05 | $0.01 (with ML) |
| **Scalability** | Horizontal (add workers) | Horizontal (add workers) |
| **Availability** | 99.9% | 99.5% (scheduled) |

---

## 🚀 Scaling Strategy

### **Current Setup** (Small scale)
- 1 Spark Master
- 2 Spark Workers (2 cores, 2GB each)
- **Capacity**: ~100 concurrent sessions

### **Medium Scale** (Add more workers)
- 1 Spark Master
- 5 Spark Workers (4 cores, 4GB each)
- **Capacity**: ~500 concurrent sessions

### **Large Scale** (Cluster mode)
- 3 Spark Masters (HA)
- 10+ Spark Workers (8 cores, 8GB each)
- **Capacity**: ~5000+ concurrent sessions

---

## 📊 Complete Timeline: One Practice Session

```
00:00  User clicks "Start Practice Session"
00:01  interview_service creates session, publishes to Kafka
00:02  Spark receives event
00:03  Spark generates 5 questions (calls OpenAI)
00:07  Questions saved to DB, sent to frontend
00:08  User sees first question

00:10  User answers question 1 (2 min)
02:10  Answer submitted, published to Kafka
02:11  Spark receives answer
02:12  Spark analyzes answer (calls OpenAI)
02:16  Feedback saved, sent to frontend
02:17  User sees feedback for Q1

[Repeat for questions 2-5: ~10 minutes total]

12:17  User answers last question
14:17  All answers analyzed
14:18  Session marked complete, published to Kafka
14:19  Spark receives completion event
14:20  Spark generates comprehensive report
14:25  Report saved, sent to frontend
14:26  User sees full session report 🎉

Total: ~14-15 minutes for 5-question session
```

---

## ✅ Summary: How It All Works

1. **User Action** → Interview Service → **Kafka**
2. **Kafka** → Spark Streaming (24/7) → **Processing**
3. **Processing** → OpenAI/ML Models → **Results**
4. **Results** → Redis Cache + **Kafka**
5. **Kafka** → Interview Service → **WebSocket** → User
6. **Airflow** schedules batch jobs → **Spark** → Analytics Reports

**Result**: ⚡ Fast, 📊 Scalable, 💰 Cost-effective AI-powered interview analysis!
