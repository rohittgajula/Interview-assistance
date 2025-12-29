# Analytics Service

A microservice for AI-powered interview analysis using Apache Airflow, Kafka, and Redis.

## Overview

The Analytics Service handles all AI-powered analysis for the Interview Assistance platform:
- **Question Generation**: Generate interview questions based on job roles
- **Answer Feedback**: Analyze user answers and provide detailed feedback
- **Session Reports**: Create comprehensive session summaries

## Architecture

```
┌──────────────────┐      Kafka Topics       ┌──────────────────┐
│interview_service │ ───────────────────────>│analytics_service │
│                  │                          │                  │
│ - Creates session│  practice-session.created│ - Consumes events│
│ - User answers   │  answer.submitted       │ - Triggers AI    │
│ - Stores results │  session.completed      │ - Sends results  │
└──────────────────┘                          └──────────────────┘
                                                       │
                                              ┌────────┴────────┐
                                              │                 │
                                         ┌────▼───┐      ┌─────▼────┐
                                         │ Airflow│      │  Redis   │
                                         │  DAGs  │      │  Cache   │
                                         └────────┘      └──────────┘
                                              │
                                      ┌───────┴────────┐
                                      │                │
                                  ┌───▼───┐      ┌────▼────┐
                                  │OpenAI │      │Anthropic│
                                  └───────┘      └─────────┘
```

## Features

- ✅ Event-driven architecture with Kafka
- ✅ Apache Airflow for workflow orchestration
- ✅ Redis caching for AI responses
- ✅ Multiple AI provider support (OpenAI, Anthropic)
- ✅ Structured logging with JSON format
- ✅ No database required (stateless service)
- ✅ Automatic retries and fault tolerance

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (or Anthropic API key)
- Running Kafka instance

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 2. Start Services

```bash
# Build and start all containers
docker-compose up --build

# Or run in detached mode
docker-compose up -d
```

### 3. Access Airflow UI

Open http://localhost:8081 in your browser:
- **Username**: admin
- **Password**: admin

### 4. Verify Services

```bash
# Check Airflow scheduler
docker-compose logs -f airflow-scheduler

# Check Kafka consumer
docker-compose logs -f kafka-consumer

# Check Redis
docker exec -it analytics-redis redis-cli ping
```

## Kafka Topics

### Consumed Topics (from interview_service):

| Topic | Description | Payload |
|-------|-------------|---------|
| `practice-session.created` | New session created | `{session_id, job_role, num_questions}` |
| `answer.submitted` | User submitted answer | `{question_id, answer_transcript, expected_topics}` |
| `session.completed` | Session finished | `{session_id, questions[]}` |

### Published Topics (to interview_service):

| Topic | Description | Payload |
|-------|-------------|---------|
| `question.generated` | AI generated question | `{session_id, question_text, category, expected_topics}` |
| `feedback.generated` | AI feedback ready | `{question_id, scores, feedback_text, strengths, improvements}` |
| `report.generated` | Session report ready | `{session_id, overall_score, summary, recommendations}` |

## Airflow DAGs

Three main DAGs orchestrate the AI workflows:

1. **`question_generation`** - Generate interview questions
2. **`feedback_analysis`** - Analyze answers and provide feedback
3. **`report_generation`** - Create comprehensive session reports

Each DAG:
- Triggered via Airflow API from Kafka consumers
- Retries up to 2 times on failure
- Caches results in Redis
- Publishes results back to Kafka

## Project Structure

```
analytics_service/
├── config/                 # Configuration
│   ├── __init__.py
│   └── settings.py
├── dags/                   # Airflow DAGs
│   ├── question_generation_dag.py
│   ├── feedback_analysis_dag.py
│   └── report_generation_dag.py
├── kafka_consumers/        # Kafka event consumers
│   ├── base_consumer.py
│   ├── session_consumer.py
│   └── answer_consumer.py
├── kafka_producers/        # Kafka event producers
│   └── producer.py
├── ai_providers/           # AI provider integrations
│   ├── base_provider.py
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── provider_factory.py
├── services/               # Business logic
│   ├── question_service.py
│   ├── feedback_service.py
│   └── report_service.py
├── utils/                  # Utilities
│   ├── redis_client.py
│   └── logger.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── main.py                # Kafka consumer entry point
└── README.md
```

## Configuration

Key environment variables (in `.env`):

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Redis
REDIS_HOST=redis-analytics
REDIS_PORT=6379

# AI Providers
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
DEFAULT_AI_PROVIDER=openai

# Airflow
AIRFLOW__CORE__FERNET_KEY=your-fernet-key
```

## Development

### Run Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start Kafka consumers
python main.py

# In another terminal, start Airflow
airflow standalone
```

### Add New AI Provider

1. Create provider class in `ai_providers/`
2. Implement `BaseAIProvider` interface
3. Register in `provider_factory.py`
4. Update settings with new provider type

### Testing

```bash
# Send test message to Kafka
kafka-console-producer --broker-list localhost:9092 --topic practice-session.created

# Paste JSON payload:
{
  "session_id": "test-123",
  "job_role": {"title": "Backend Developer", "required_skills": ["Python"]},
  "num_questions": 3
}

# Watch logs
docker-compose logs -f kafka-consumer
```

## Monitoring

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f kafka-consumer

# Airflow scheduler
docker-compose logs -f airflow-scheduler
```

### Airflow UI

- **URL**: http://localhost:8081
- Monitor DAG runs, task success/failure
- View task logs and execution times
- Manually trigger DAGs for testing

### Redis

```bash
# Connect to Redis CLI
docker exec -it analytics-redis redis-cli

# Check cached questions
KEYS question:*

# Check cached feedback
KEYS feedback:*

# Get cache entry
GET "question:session-id:1"
```

## Troubleshooting

### Kafka Connection Issues

```bash
# Check Kafka is running
docker ps | grep kafka

# Test Kafka connectivity from analytics service
docker exec -it analytics-kafka-consumer kafka-topics --list --bootstrap-server kafka:9092
```

### Redis Connection Issues

```bash
# Check Redis is running
docker exec -it analytics-redis redis-cli ping

# Should return: PONG
```

### Airflow Not Starting

```bash
# Reset Airflow database
docker-compose down
docker volume rm analytics_service_postgres_airflow_data
docker-compose up airflow-init
docker-compose up
```

### AI Provider Errors

```bash
# Check API keys are set
docker exec analytics-kafka-consumer env | grep API_KEY

# Test OpenAI connection
docker exec analytics-kafka-consumer python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

## Production Considerations

### Scaling

- Scale Kafka consumers: `docker-compose up --scale kafka-consumer=3`
- Use Airflow CeleryExecutor for distributed task execution
- Add Redis Cluster for high availability

### Security

- ✅ Encrypt API keys in environment
- ✅ Use Airflow RBAC for access control
- ✅ Enable Kafka SSL/SASL
- ✅ Use Redis AUTH

### Monitoring

- Add Prometheus metrics export
- Integrate with Grafana dashboards
- Set up alerts for DAG failures
- Monitor AI provider costs

## API Costs

Estimated costs per session (using GPT-4):
- Question generation (5 questions): ~$0.02
- Feedback analysis (5 answers): ~$0.10
- Report generation: ~$0.03
- **Total**: ~$0.15 per session

Use caching to reduce costs by 60-80%!

## Contributing

1. Create feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit pull request

## License

Proprietary - Interview Assistance Platform

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review Airflow UI: http://localhost:8081
- Check Kafka topics: `kafka-console-consumer --bootstrap-server kafka:9092 --topic <topic> --from-beginning`
