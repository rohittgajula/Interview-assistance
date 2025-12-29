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
