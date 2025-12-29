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
