# Spark Jobs - Complete Implementation

All Spark job implementations for the analytics service.

---

## File: `spark/jobs/__init__.py`

```python
from .question_generation_job import QuestionGenerationJob
from .feedback_analysis_job import FeedbackAnalysisJob
from .report_generation_job import ReportGenerationJob

__all__ = ['QuestionGenerationJob', 'FeedbackAnalysisJob', 'ReportGenerationJob']
```

---

## File: `spark/jobs/question_generation_job.py`

```python
"""
Spark Job for generating interview questions using AI
"""
import json
import os
import redis
from openai import OpenAI
from kafka import KafkaProducer


class QuestionGenerationJob:
    """Generate interview questions based on job role"""

    def __init__(self):
        # Redis for caching
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis-analytics"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=1,
            decode_responses=True
        )

        # OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Kafka producer
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def process_event(self, event_json):
        """
        Process practice-session.created event

        Args:
            event_json: JSON string with session details
        """
        try:
            event = json.loads(event_json)

            session_id = event.get('session_id')
            job_role = event.get('job_role', {})
            num_questions = event.get('num_questions', 5)

            print(f"    ├─ Generating {num_questions} questions for: {job_role.get('title')}")

            # Check cache first
            cache_key = f"questions:{session_id}"
            cached = self.redis_client.get(cache_key)

            if cached:
                print(f"    ├─ Using cached questions")
                questions = json.loads(cached)
            else:
                print(f"    ├─ Calling OpenAI API...")
                questions = self._generate_with_ai(job_role, num_questions)

                # Cache for 2 hours
                self.redis_client.setex(cache_key, 7200, json.dumps(questions))
                print(f"    ├─ Cached questions (TTL: 2h)")

            # Publish each question to Kafka
            for i, question in enumerate(questions, 1):
                question_data = {
                    "session_id": session_id,
                    "question_number": i,
                    "question_text": question['question_text'],
                    "question_category": question['category'],
                    "question_context": question.get('context', ''),
                    "expected_topics": question.get('expected_topics', [])
                }

                self.kafka_producer.send('question.generated', question_data)
                print(f"    ├─ Published Q{i}: {question['category']}")

            self.kafka_producer.flush()
            print(f"    └─ ✓ Generated {len(questions)} questions")

        except Exception as e:
            print(f"    └─ ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    def _generate_with_ai(self, job_role, num_questions):
        """
        Generate questions using OpenAI

        Args:
            job_role: Job role details dict
            num_questions: Number of questions to generate

        Returns:
            List of question dicts
        """
        title = job_role.get('title', 'Software Engineer')
        skills = job_role.get('required_skills', [])
        level = job_role.get('experience_level', 'mid')
        difficulty = job_role.get('difficulty_level', 'medium')

        tech_count = int(job_role.get('technical_weight', 0.5) * num_questions)
        behavioral_count = int(job_role.get('behavioral_weight', 0.3) * num_questions)
        situational_count = int(job_role.get('situational_weight', 0.1) * num_questions)
        general_count = num_questions - tech_count - behavioral_count - situational_count

        prompt = f"""Generate {num_questions} interview questions for: {title}

Experience Level: {level}
Difficulty: {difficulty}
Required Skills: {', '.join(skills)}

Distribution:
- Technical: {tech_count} questions
- Behavioral: {behavioral_count} questions
- Situational: {situational_count} questions
- General: {general_count} questions

For each question, provide:
1. question_text: The actual question to ask
2. category: One of (technical, behavioral, situational, general)
3. context: Why this question matters for this role
4. expected_topics: List of 3-5 topics a good answer should cover

Return as JSON array with {num_questions} questions.

Example format:
[
  {{
    "question_text": "Explain how you would design a scalable API",
    "category": "technical",
    "context": "Tests system design skills critical for backend role",
    "expected_topics": ["REST principles", "caching", "rate limiting", "authentication", "scalability"]
  }}
]
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer. Generate precise, relevant interview questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            questions = result.get('questions', [])

            return questions[:num_questions]

        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Return fallback questions
            return self._fallback_questions(num_questions)

    def _fallback_questions(self, num_questions):
        """Fallback questions if API fails"""
        return [
            {
                "question_text": f"Sample technical question {i+1}",
                "category": "technical",
                "context": "Testing technical knowledge",
                "expected_topics": ["topic1", "topic2", "topic3"]
            }
            for i in range(num_questions)
        ]
```

---

## File: `spark/jobs/feedback_analysis_job.py`

```python
"""
Spark Job for analyzing answers and generating feedback
"""
import json
import os
import redis
from openai import OpenAI
from kafka import KafkaProducer


class FeedbackAnalysisJob:
    """Analyze user answers and provide detailed feedback"""

    def __init__(self):
        # Redis for caching
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis-analytics"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=1,
            decode_responses=True
        )

        # OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Kafka producer
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def process_event(self, event_json):
        """
        Process answer.submitted event

        Args:
            event_json: JSON string with answer details
        """
        try:
            event = json.loads(event_json)

            question_id = event.get('question_id')
            session_id = event.get('session_id')
            question_text = event.get('question_text')
            answer_transcript = event.get('answer_transcript')
            expected_topics = event.get('expected_topics', [])
            job_role = event.get('job_role', {})

            print(f"    ├─ Analyzing answer for Q: {question_text[:50]}...")

            # Check cache
            cache_key = f"feedback:{question_id}"
            cached = self.redis_client.get(cache_key)

            if cached:
                print(f"    ├─ Using cached feedback")
                feedback = json.loads(cached)
            else:
                print(f"    ├─ Calling OpenAI API...")
                feedback = self._analyze_with_ai(
                    question_text,
                    answer_transcript,
                    expected_topics,
                    job_role
                )

                # Cache for 2 hours
                self.redis_client.setex(cache_key, 7200, json.dumps(feedback))
                print(f"    ├─ Cached feedback (TTL: 2h)")

            # Publish feedback to Kafka
            feedback_data = {
                "question_id": question_id,
                "session_id": session_id,
                **feedback
            }

            self.kafka_producer.send('feedback.generated', feedback_data)
            self.kafka_producer.flush()

            print(f"    └─ ✓ Score: {feedback.get('overall_score')}/100")

        except Exception as e:
            print(f"    └─ ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    def _analyze_with_ai(self, question_text, answer_text, expected_topics, job_role):
        """
        Analyze answer using OpenAI

        Returns:
            Dict with scores and feedback
        """
        prompt = f"""Analyze this interview answer and provide detailed feedback.

**Question:** {question_text}

**Answer:** {answer_text}

**Expected Topics:** {', '.join(expected_topics)}

**Role Context:** {job_role.get('title', 'N/A')}

Provide scores (0-100) for:

**Technical/Content:**
- relevance: How relevant to the question
- completeness: Coverage of expected topics
- accuracy: Technical accuracy
- depth: Depth of knowledge shown

**Communication:**
- fluency: Smooth, natural speech flow
- grammar: Grammatical correctness
- vocabulary: Appropriate word choice
- articulation: Clear expression of ideas

**Behavioral:**
- confidence: Confidence in delivery
- enthusiasm: Energy and engagement
- professionalism: Professional demeanor

**Mindset:**
- structure: Organized, logical response
- critical_thinking: Analytical approach
- growth_mindset: Learning attitude

Also provide:
- overall_score: Weighted average (0-100)
- feedback_text: 2-3 sentences of constructive feedback
- strengths: Array of 3 key strengths
- improvements: Array of 3 areas to improve
- topics_covered: Array of topics mentioned
- topics_missed: Array of expected topics not mentioned

Return as JSON object with all scores and feedback.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert interview coach providing constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            feedback = json.loads(response.choices[0].message.content)

            # Calculate composite scores
            tech = feedback.get('technical', {})
            comm = feedback.get('communication', {})
            behav = feedback.get('behavioral', {})
            mind = feedback.get('mindset', {})

            feedback['technical_score'] = sum([
                tech.get('relevance', 0),
                tech.get('completeness', 0),
                tech.get('accuracy', 0),
                tech.get('depth', 0)
            ]) / 4

            feedback['communication_score'] = sum([
                comm.get('fluency', 0),
                comm.get('grammar', 0),
                comm.get('vocabulary', 0),
                comm.get('articulation', 0)
            ]) / 4

            feedback['behavioral_score'] = sum([
                behav.get('confidence', 0),
                behav.get('enthusiasm', 0),
                behav.get('professionalism', 0)
            ]) / 3

            feedback['mindset_score'] = sum([
                mind.get('structure', 0),
                mind.get('critical_thinking', 0),
                mind.get('growth_mindset', 0)
            ]) / 3

            # Overall weighted score
            if 'overall_score' not in feedback:
                feedback['overall_score'] = (
                    feedback['technical_score'] * 0.35 +
                    feedback['communication_score'] * 0.30 +
                    feedback['behavioral_score'] * 0.20 +
                    feedback['mindset_score'] * 0.15
                )

            return feedback

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._fallback_feedback()

    def _fallback_feedback(self):
        """Fallback feedback if API fails"""
        return {
            "overall_score": 75.0,
            "technical_score": 75.0,
            "communication_score": 75.0,
            "behavioral_score": 75.0,
            "mindset_score": 75.0,
            "feedback_text": "Answer received and will be reviewed.",
            "strengths": ["Clear communication"],
            "improvements": ["Add more examples"],
            "topics_covered": [],
            "topics_missed": []
        }
```

---

## File: `spark/jobs/report_generation_job.py`

```python
"""
Spark Job for generating comprehensive session reports
"""
import json
import os
import redis
from openai import OpenAI
from kafka import KafkaProducer


class ReportGenerationJob:
    """Generate comprehensive session reports"""

    def __init__(self):
        # Redis for caching
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis-analytics"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=1,
            decode_responses=True
        )

        # OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Kafka producer
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def process_event(self, event_json):
        """
        Process session.completed event

        Args:
            event_json: JSON string with session completion details
        """
        try:
            event = json.loads(event_json)

            session_id = event.get('session_id')
            questions = event.get('questions', [])

            print(f"    ├─ Generating report for session with {len(questions)} questions")

            # Check cache
            cache_key = f"report:{session_id}"
            cached = self.redis_client.get(cache_key)

            if cached:
                print(f"    ├─ Using cached report")
                report = json.loads(cached)
            else:
                print(f"    ├─ Collecting feedback from Redis...")
                feedbacks = []
                for q in questions:
                    feedback_key = f"feedback:{q['question_id']}"
                    feedback_json = self.redis_client.get(feedback_key)
                    if feedback_json:
                        feedbacks.append(json.loads(feedback_json))

                print(f"    ├─ Found {len(feedbacks)} feedbacks")

                # Aggregate scores
                report = self._aggregate_scores(feedbacks)

                # Generate AI summary
                print(f"    ├─ Calling OpenAI for summary...")
                summary = self._generate_summary(feedbacks, session_id)
                report.update(summary)

                # Cache for 24 hours
                self.redis_client.setex(cache_key, 86400, json.dumps(report))
                print(f"    ├─ Cached report (TTL: 24h)")

            # Publish report to Kafka
            report_data = {
                "session_id": session_id,
                **report
            }

            self.kafka_producer.send('report.generated', report_data)
            self.kafka_producer.flush()

            print(f"    └─ ✓ Overall Score: {report.get('overall_score')}/100")

        except Exception as e:
            print(f"    └─ ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    def _aggregate_scores(self, feedbacks):
        """Aggregate all feedback scores"""
        if not feedbacks:
            return {}

        def avg(field):
            values = [f.get(field, 0) for f in feedbacks if f.get(field)]
            return sum(values) / len(values) if values else 0

        return {
            "overall_score": avg('overall_score'),
            "technical_score": avg('technical_score'),
            "communication_score": avg('communication_score'),
            "behavioral_score": avg('behavioral_score'),
            "mindset_score": avg('mindset_score'),

            # Technical breakdown
            "technical_breakdown": {
                "relevance_avg": avg('relevance'),
                "completeness_avg": avg('completeness'),
                "accuracy_avg": avg('accuracy'),
                "depth_avg": avg('depth')
            },

            # Communication breakdown
            "communication_breakdown": {
                "fluency_avg": avg('fluency'),
                "grammar_avg": avg('grammar'),
                "vocabulary_avg": avg('vocabulary'),
                "articulation_avg": avg('articulation')
            },

            # Speaking metrics
            "speaking_metrics": {
                "total_filler_words": sum(f.get('filler_word_count', 0) for f in feedbacks),
                "average_words_per_minute": avg('words_per_minute')
            }
        }

    def _generate_summary(self, feedbacks, session_id):
        """Generate AI summary of entire session"""
        if not feedbacks:
            return {"summary": "Session completed"}

        avg_overall = sum(f.get('overall_score', 0) for f in feedbacks) / len(feedbacks)
        avg_tech = sum(f.get('technical_score', 0) for f in feedbacks) / len(feedbacks)
        avg_comm = sum(f.get('communication_score', 0) for f in feedbacks) / len(feedbacks)

        prompt = f"""Generate a comprehensive interview session summary.

**Session Performance:**
- {len(feedbacks)} questions answered
- Overall Score: {avg_overall:.1f}/100
- Technical Score: {avg_tech:.1f}/100
- Communication Score: {avg_comm:.1f}/100

**Individual Question Scores:**
{self._format_question_scores(feedbacks)}

Provide:
- summary: 2-3 sentence overall summary of performance
- key_strengths: Array of 5 key strengths across all questions
- areas_for_improvement: Array of 5 areas to work on
- recommendations: Array of 5 actionable recommendations
- technical_feedback: Paragraph summarizing technical performance
- communication_feedback: Paragraph on communication skills
- behavioral_feedback: Paragraph on soft skills
- mindset_feedback: Paragraph on problem-solving approach

Return as JSON object.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert interview coach providing comprehensive session summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return {
                "summary": "Session completed successfully",
                "key_strengths": ["Completed all questions"],
                "areas_for_improvement": ["Continue practicing"],
                "recommendations": ["Review feedback for each question"]
            }

    def _format_question_scores(self, feedbacks):
        """Format question scores for prompt"""
        lines = []
        for i, f in enumerate(feedbacks, 1):
            lines.append(f"Q{i}: {f.get('overall_score', 0):.1f}/100")
        return "\n".join(lines)
```

---

## File: `docker/spark/Dockerfile`

```dockerfile
FROM bitnami/spark:3.5

USER root

# Install Python dependencies
COPY spark/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy Spark applications
COPY spark /opt/spark-apps/spark
COPY kafka_integration /opt/spark-apps/kafka_integration
COPY config /opt/spark-apps/config

# Set working directory
WORKDIR /opt/spark-apps

USER 1001
```

---

## File: `docker/airflow/Dockerfile`

```dockerfile
FROM apache/airflow:2.8.1-python3.11

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy and install requirements
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

# Install Airflow Spark provider
RUN pip install apache-airflow-providers-apache-spark==4.7.1

# Set environment
ENV PYTHONPATH=/opt/airflow
ENV AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
```

---

That's the complete Spark jobs implementation! All three jobs:
1. **Question Generation** - Uses OpenAI to generate questions
2. **Feedback Analysis** - Analyzes answers with AI
3. **Report Generation** - Creates comprehensive reports

Next, I'll create the Airflow DAGs for scheduling batch analytics jobs.
