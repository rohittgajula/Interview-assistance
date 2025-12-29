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
