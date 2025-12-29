# Interview Service API Documentation

## Overview
This document provides a complete list of all REST API endpoints needed for the Interview Service. The APIs are organized by feature area and include request/response schemas, authentication requirements, and permission levels.

**Base URL:** `/api/v1/`

**Authentication:** All endpoints except health check require JWT Bearer token in Authorization header:
```
Authorization: Bearer <token>
```

**API Documentation UI:**
- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`
- OpenAPI Schema: `/api/schema/`

---

## Permission Classes Reference

All API endpoints use custom permission classes defined in `interviews/permissions.py`. Below is a complete reference:

### Basic Permissions
- **`IsAuthenticated`** - Allows only authenticated users
- **`AllowAny`** - Allows unrestricted access (public endpoints)
- **`IsActiveUser`** - Allows only active authenticated users
- **`ReadOnly`** - Allows read-only access (GET, HEAD, OPTIONS)

### Role-Based Permissions
- **`IsCandidate`** - Allows only candidates
- **`IsInterviewer`** - Allows only interviewers
- **`IsOrgAdmin`** - Allows only organization admins
- **`IsInterviewerOrCandidate`** - Allows both interviewers and candidates
- **`IsInterviewerOrOrgAdmin`** - Allows interviewers and org admins
- **`IsCandidateOrOrgAdmin`** - Allows candidates and org admins

### Object-Level Permissions
- **`IsOwner`** - Allows only the owner of the resource
- **`IsOwnerOrReadOnly`** - Owner can edit, others can read
- **`IsOwnerOrInterviewer`** - Owner or interviewer of the session
- **`IsInterviewerForLiveSession`** - Interviewer of a specific live session

### Composite Permissions
- **`IsCandidateOrReadOnly`** - Candidates can write, all authenticated users can read
- **`CanScheduleLiveInterview`** - Interviewers and org admins can schedule (POST), others can read
- **`CanManageJobRoles`** - Org admins can write, all authenticated users can read
- **`CanManageAIProviders`** - Org admins only (full CRUD)
- **`CanViewAnalytics`** - Users can view own analytics, org admins can view all
- **`IsAuthenticatedOrCreateOnly`** - Allow POST without auth, require auth for other methods

### Testing Permission (DO NOT USE IN PRODUCTION)
- **`IsTestUser`** - Always allows access (for testing only)

---

## Table of Contents
1. [Authentication & Profile APIs](#1-authentication--profile-apis)
2. [Job Role APIs](#2-job-role-apis)
3. [Practice Session APIs (Solo AI Practice)](#3-practice-session-apis-solo-ai-practice)
4. [Live Interview APIs (Two-Person)](#4-live-interview-apis-two-person)
5. [Progress & Analytics APIs](#5-progress--analytics-apis)
6. [AI/Speech Provider Management APIs (Admin)](#6-aispeech-provider-management-apis-admin)
7. [WebSocket API](#7-websocket-api)
8. [Health & Utility APIs](#8-health--utility-apis)

---

## 1. Authentication & Profile APIs

### 1.1 Get Current User Profile
**Endpoint:** `GET /api/v1/profiles/me/`

**Permission:** `IsAuthenticated`

**Description:** Retrieve the current authenticated user's interview profile

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "role": "candidate",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "bio": "Software engineer...",
  "avatar_url": "https://minio.../avatar.jpg",
  "resume_url": "https://minio.../resume.pdf",
  "current_job_title": "Senior Developer",
  "current_company": "Tech Corp",
  "experience_years": 5,
  "skills": ["Python", "Django", "React"],
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe",
  "portfolio_url": "https://johndoe.com",
  "preferred_language": "en",
  "user_timezone": "America/New_York",
  "email_notifications": true,
  "created_at": "2024-01-01T00:00:00Z",
  "profile_updated_at": "2024-01-15T00:00:00Z"
}
```

---

### 1.2 Update Current User Profile (Full)
**Endpoint:** `PUT /api/v1/profiles/me/`

**Permission:** `IsAuthenticated`

**Description:** Complete update of user profile (all fields)

**Request Body:**
```json
{
  "full_name": "John Doe",
  "phone": "+1234567890",
  "bio": "Experienced software engineer...",
  "current_job_title": "Senior Developer",
  "current_company": "Tech Corp",
  "experience_years": 5,
  "skills": ["Python", "Django", "React", "PostgreSQL"],
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe",
  "portfolio_url": "https://johndoe.com",
  "preferred_language": "en",
  "user_timezone": "America/New_York",
  "email_notifications": true
}
```

**Response:** Same as 1.1 (updated profile)

---

### 1.3 Update Current User Profile (Partial)
**Endpoint:** `PATCH /api/v1/profiles/me/`

**Permission:** `IsAuthenticated`

**Description:** Partial update of user profile (only provided fields)

**Request Body:**
```json
{
  "skills": ["Python", "Django", "FastAPI"],
  "experience_years": 6
}
```

**Response:** Same as 1.1 (updated profile)

---

### 1.4 Upload Avatar
**Endpoint:** `POST /api/v1/profiles/me/avatar/`

**Permission:** `IsAuthenticated`

**Content-Type:** `multipart/form-data`

**Description:** Upload user avatar image to MinIO

**Request:**
```
Form data:
- avatar: <file> (image/jpeg, image/png, max 5MB)
```

**Response:**
```json
{
  "avatar_url": "https://minio.../user-profiles/uuid/avatar.jpg",
  "message": "Avatar uploaded successfully"
}
```

---

### 1.5 Upload Resume
**Endpoint:** `POST /api/v1/profiles/me/resume/`

**Permission:** `IsAuthenticated`

**Content-Type:** `multipart/form-data`

**Description:** Upload user resume (PDF) to MinIO

**Request:**
```
Form data:
- resume: <file> (application/pdf, max 2MB)
```

**Response:**
```json
{
  "resume_url": "https://minio.../user-documents/uuid/resume.pdf",
  "message": "Resume uploaded successfully"
}
```

---

### 1.6 Delete Avatar
**Endpoint:** `DELETE /api/v1/profiles/me/avatar/`

**Permission:** `IsAuthenticated`

**Description:** Delete user avatar from MinIO and profile

**Response:**
```json
{
  "message": "Avatar deleted successfully"
}
```

---

### 1.7 Delete Resume
**Endpoint:** `DELETE /api/v1/profiles/me/resume/`

**Permission:** `IsAuthenticated`

**Description:** Delete user resume from MinIO and profile

**Response:**
```json
{
  "message": "Resume deleted successfully"
}
```

---

### 1.8 Get Public Profile
**Endpoint:** `GET /api/v1/profiles/{user_id}/`

**Permission:** `IsAuthenticated`

**Description:** Get another user's public profile (limited fields)

**Response:**
```json
{
  "id": "uuid",
  "username": "janedoe",
  "full_name": "Jane Doe",
  "avatar_url": "https://minio.../avatar.jpg",
  "current_job_title": "Software Architect",
  "current_company": "Innovation Labs",
  "experience_years": 8,
  "skills": ["Python", "Architecture", "AWS"],
  "bio": "Passionate about building scalable systems..."
}
```

---

## 2. Job Role APIs

### 2.1 List Job Roles
**Endpoint:** `GET /api/v1/job-roles/`

**Permission:** `CanManageJobRoles` (read: all authenticated users)

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20, max: 100)
- `experience_level`: Filter by level (entry, mid, senior, lead)
- `industry`: Filter by industry
- `is_active`: Filter active roles (true/false)
- `search`: Search in title/description

**Description:** List all job roles with filtering and pagination

**Response:**
```json
{
  "count": 45,
  "next": "https://.../api/v1/job-roles/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Senior Backend Developer",
      "description": "Build scalable microservices...",
      "required_skills": ["Python", "Django", "PostgreSQL"],
      "preferred_skills": ["Docker", "Kubernetes"],
      "experience_level": "senior",
      "industry": "fintech",
      "difficulty_level": "hard",
      "technical_weight": 0.5,
      "behavioral_weight": 0.25,
      "situational_weight": 0.15,
      "general_weight": 0.1,
      "key_topics": ["system design", "API design", "databases"],
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### 2.2 Create Job Role
**Endpoint:** `POST /api/v1/job-roles/`

**Permission:** `CanManageJobRoles` (write: org admins only)

**Description:** Create a new job role configuration

**Request Body:**
```json
{
  "title": "Senior Backend Developer",
  "description": "Build scalable microservices...",
  "required_skills": ["Python", "Django", "PostgreSQL", "Redis"],
  "preferred_skills": ["Docker", "Kubernetes", "AWS"],
  "experience_level": "senior",
  "industry": "fintech",
  "company_context": "Fast-paced startup environment",
  "difficulty_level": "hard",
  "technical_weight": 0.5,
  "behavioral_weight": 0.25,
  "situational_weight": 0.15,
  "general_weight": 0.1,
  "key_topics": ["system design", "API design", "databases", "caching"],
  "topics_to_avoid": ["frontend", "mobile"],
  "custom_instructions": "Focus on distributed systems experience"
}
```

**Response:** Same as list item above

---

### 2.3 Get Job Role Details
**Endpoint:** `GET /api/v1/job-roles/{id}/`

**Permission:** `CanManageJobRoles` (read: all authenticated users)

**Description:** Retrieve detailed information about a specific job role

**Response:** Same as list item in 2.1

---

### 2.4 Update Job Role
**Endpoint:** `PUT /api/v1/job-roles/{id}/`

**Permission:** `CanManageJobRoles` (write: org admins only)

**Description:** Update an existing job role

**Request Body:** Same as 2.2

**Response:** Updated job role object

---

### 2.5 Delete Job Role (Soft Delete)
**Endpoint:** `DELETE /api/v1/job-roles/{id}/`

**Permission:** `CanManageJobRoles` (write: org admins only)

**Description:** Soft delete job role (sets is_active=False)

**Response:**
```json
{
  "message": "Job role deactivated successfully"
}
```

---

## 3. Practice Session APIs (Solo AI Practice)

**Architecture:** Practice sessions use a **hybrid REST + WebSocket approach**:
- **REST APIs:** Session management (create, list, get details, get reports, cancel)
- **WebSocket:** Real-time conversational flow (questions, answers, feedback)

This architecture provides a **natural conversation experience** with low latency (10-50ms per message) while keeping session management simple via REST.

---

### REST Endpoints

### 3.1 List Practice Sessions
**Endpoint:** `GET /api/v1/practice-sessions/`

**Permission:** `IsAuthenticated` (own sessions only)

**Query Parameters:**
- `page`, `page_size`: Pagination
- `status`: Filter by status (scheduled, in_progress, completed, cancelled)
- `job_role`: Filter by job role ID
- `ordering`: Sort by field (e.g., `-created_at`, `scheduled_at`)

**Description:** List user's practice sessions

**Response:**
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "user": "uuid",
      "job_role": {
        "id": "uuid",
        "title": "Senior Backend Developer"
      },
      "status": "completed",
      "duration_minutes": 30,
      "num_questions": 5,
      "scheduled_at": null,
      "started_at": "2024-01-15T10:00:00Z",
      "ended_at": "2024-01-15T10:32:00Z",
      "actual_duration": 32,
      "full_audio_url": "https://minio.../recording.mp3",
      "websocket_url": "wss://.../ws/practice-sessions/uuid/?token=<jwt>",
      "created_at": "2024-01-15T09:45:00Z"
    }
  ]
}
```

---

### 3.2 Create Practice Session
**Endpoint:** `POST /api/v1/practice-sessions/`

**Permission:** `IsCandidate`

**Description:** Create a new practice session and get WebSocket URL to start practicing

**Request Body:**
```json
{
  "job_role": "uuid",
  "duration_minutes": 30,
  "num_questions": 5,
  "scheduled_at": "2024-01-20T14:00:00Z"  // Optional, can start immediately
}
```

**Response:**
```json
{
  "id": "uuid",
  "user": "uuid",
  "job_role": "uuid",
  "status": "scheduled",
  "duration_minutes": 30,
  "num_questions": 5,
  "scheduled_at": "2024-01-20T14:00:00Z",
  "websocket_url": "wss://.../ws/practice-sessions/uuid/?token=<jwt>",
  "created_at": "2024-01-15T12:00:00Z"
}
```

**Next Steps:** Connect to the WebSocket URL to start the practice session.

---

### 3.3 Get Practice Session Details
**Endpoint:** `GET /api/v1/practice-sessions/{id}/`

**Permission:** `IsOwner` (session owner)

**Description:** Get detailed information about a practice session

**Response:**
```json
{
  "id": "uuid",
  "user": "uuid",
  "job_role": {
    "id": "uuid",
    "title": "Senior Backend Developer",
    "experience_level": "senior"
  },
  "status": "in_progress",
  "duration_minutes": 30,
  "num_questions": 5,
  "scheduled_at": null,
  "started_at": "2024-01-15T10:00:00Z",
  "ended_at": null,
  "actual_duration": null,
  "full_audio_url": "",
  "questions_count": 3,
  "answered_count": 2,
  "websocket_url": "wss://.../ws/practice-sessions/uuid/?token=<jwt>",
  "created_at": "2024-01-15T09:55:00Z",
  "updated_at": "2024-01-15T10:15:00Z"
}
```

---

### 3.4 Delete Practice Session (Cancel)
**Endpoint:** `DELETE /api/v1/practice-sessions/{id}/`

**Permission:** `IsOwner` (session owner)

**Description:** Cancel a practice session (only if not started)

**Response:**
```json
{
  "message": "Practice session cancelled successfully"
}
```

---

### 3.5 List Session Questions
**Endpoint:** `GET /api/v1/practice-sessions/{id}/questions/`

**Permission:** `IsOwner` (session owner)

**Description:** List all questions in the session with their feedback (available after session completes)

**Response:**
```json
{
  "session_id": "uuid",
  "total_questions": 5,
  "answered_questions": 5,
  "questions": [
    {
      "id": "uuid",
      "question_number": 1,
      "question_text": "Explain REST vs GraphQL",
      "question_category": "technical",
      "asked_at": "2024-01-15T10:01:00Z",
      "answered_at": "2024-01-15T10:03:30Z",
      "answer_transcript": "REST uses HTTP methods...",
      "answer_audio_url": "https://minio.../answer_1.mp3",
      "feedback": {
        "overall_score": 78.5,
        "technical_score": 82.0,
        "communication_score": 75.0,
        "behavioral_score": 80.0,
        "mindset_score": 77.0,
        "strengths": ["Clear explanation", "Good examples"],
        "improvements": ["Could elaborate on GraphQL subscriptions"],
        "ai_feedback_text": "Good understanding of core concepts..."
      }
    }
  ]
}
```

---

### 3.6 Get Session Report
**Endpoint:** `GET /api/v1/practice-sessions/{id}/report/`

**Permission:** `IsOwner` (session owner)

**Description:** Get comprehensive session report (available after session ends)

**Response:**
```json
{
  "id": "uuid",
  "session": "uuid",
  "overall_score": 79.2,
  "technical_score": 81.5,
  "communication_score": 76.8,
  "behavioral_score": 80.1,
  "mindset_score": 78.5,

  "technical_breakdown": {
    "relevance_avg": 85.0,
    "completeness_avg": 78.0,
    "accuracy_avg": 82.0,
    "depth_avg": 81.0
  },

  "communication_breakdown": {
    "fluency_avg": 78.0,
    "grammar_avg": 82.0,
    "vocabulary_avg": 75.0,
    "pronunciation_avg": 80.0,
    "articulation_avg": 74.0,
    "pace_avg": 72.0,
    "tone_avg": 77.0
  },

  "speaking_metrics": {
    "total_speaking_time": 850,
    "average_response_time": 170.0,
    "total_filler_words": 23,
    "average_words_per_minute": 145,
    "filler_word_breakdown": {
      "um": 8,
      "uh": 6,
      "like": 5,
      "you know": 4
    }
  },

  "summary": "Strong technical knowledge with good communication skills. Areas for improvement include reducing filler words and maintaining consistent speaking pace.",

  "key_strengths": [
    "Deep understanding of system design principles",
    "Clear and structured responses",
    "Good use of real-world examples"
  ],

  "areas_for_improvement": [
    "Reduce usage of filler words (23 instances)",
    "Improve response pacing - sometimes too fast",
    "Elaborate more on scalability trade-offs"
  ],

  "recommendations": [
    "Practice mock interviews to reduce filler words",
    "Work on breathing techniques to control speaking pace",
    "Study distributed systems patterns in more depth"
  ],

  "technical_feedback": "Demonstrated strong understanding of REST and GraphQL...",
  "communication_feedback": "Generally clear communication with minor pacing issues...",
  "behavioral_feedback": "Confident and professional demeanor throughout...",
  "mindset_feedback": "Good problem-solving approach and growth mindset...",

  "improvement_from_last": 5.3,
  "score_percentile": 72.5,

  "report_pdf_url": "https://minio.../reports/uuid.pdf",
  "generated_at": "2024-01-15T10:35:00Z"
}
```

---

### WebSocket API for Practice Sessions

### 3.7 Practice Session WebSocket Connection
**Endpoint:** `WS /ws/practice-sessions/{session_id}/`

**Authentication:** JWT token in query parameter

**Connection URL:**
```
wss://your-domain.com/ws/practice-sessions/{session_id}/?token=<jwt_token>
```

**Description:** Real-time bidirectional communication for conversational practice sessions. This WebSocket handles the entire interview flow: starting the session, receiving questions, submitting answers, getting instant feedback, and session completion.

**Benefits:**
- **Natural conversation flow** - Feels like talking to a real interviewer
- **Low latency** - 10-50ms per message vs 200-500ms for REST
- **Real-time audio streaming** - Stream audio chunks as you speak
- **Live transcription** - See your words transcribed in real-time
- **Instant feedback** - Get AI feedback immediately after each answer

---

#### Complete Session Flow

```javascript
// 1. Create session via REST API
const response = await fetch('/api/v1/practice-sessions/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    job_role: 'uuid',
    duration_minutes: 30,
    num_questions: 5
  })
});
const session = await response.json();

// 2. Connect to WebSocket
const ws = new WebSocket(session.websocket_url);

// 3. Wait for connection confirmation
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'connection.established') {
    // Connection successful, start the session
    ws.send(JSON.stringify({
      type: 'session.start'
    }));
  }

  if (message.type === 'session.started') {
    // Session started, first question coming...
  }

  if (message.type === 'question.asked') {
    // Display question to user
    console.log('Q' + message.data.question_number + ': ' + message.data.question_text);
    // Optionally play audio: message.data.question_audio_url
  }

  if (message.type === 'transcription.interim') {
    // Show live transcription as user speaks
    console.log('You said: ' + message.data.text);
  }

  if (message.type === 'answer.feedback') {
    // Show instant AI feedback
    console.log('Feedback: ' + message.data.ai_feedback_text);
    console.log('Score: ' + message.data.overall_score);
  }

  if (message.type === 'question.asked') {
    // Next question automatically sent after feedback
    console.log('Next Q: ' + message.data.question_text);
  }

  if (message.type === 'session.complete') {
    // All done! Show completion message
    console.log('Session complete!');
    ws.close();
  }
};

// 4. Submit answer (when user finishes speaking)
function submitAnswer(audioBlob, transcript) {
  ws.send(JSON.stringify({
    type: 'answer.submit',
    data: {
      answer_transcript: transcript,
      answer_audio_base64: await blobToBase64(audioBlob)  // Optional
    }
  }));
}

// 5. Or stream audio in real-time (advanced)
function streamAudioChunk(chunk, sequence, isFinal) {
  ws.send(JSON.stringify({
    type: 'answer.audio_chunk',
    data: {
      chunk_base64: arrayBufferToBase64(chunk),
      sequence: sequence,
      is_final: isFinal
    }
  }));
}

// 6. End session early (optional)
ws.send(JSON.stringify({ type: 'session.end' }));

// 7. Get report via REST API after session completes
const report = await fetch(`/api/v1/practice-sessions/${session.id}/report/`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

#### WebSocket Events Reference

### Client → Server Events

**3.7.1 Start Session**
```json
{
  "type": "session.start"
}
```
**Description:** Start the practice session. Triggers AI question generation and sends first question when ready.

---

**3.7.2 Submit Answer (Text + Audio)**
```json
{
  "type": "answer.submit",
  "data": {
    "answer_transcript": "REST uses HTTP methods and resources to perform CRUD operations. It's stateless and cacheable. GraphQL on the other hand allows clients to request exactly what they need...",
    "answer_audio_base64": "<base64_encoded_audio>",  // Optional
    "answer_duration_seconds": 87  // Optional
  }
}
```
**Description:** Submit answer to current question. Server will process the answer, generate feedback, and automatically send the next question.

**Response Flow:**
1. Server sends `transcription.interim` events (if audio provided)
2. Server sends `answer.feedback` with AI analysis
3. Server sends `question.asked` with next question (or `session.complete` if done)

---

**3.7.3 Submit Answer (Audio Streaming)**
```json
{
  "type": "answer.audio_chunk",
  "data": {
    "chunk_base64": "<base64_encoded_audio_chunk>",
    "sequence": 123,
    "is_final": false
  }
}
```
**Description:** Stream audio in real-time for live transcription. Send multiple chunks as user speaks, set `is_final: true` on last chunk.

---

**3.7.4 End Session**
```json
{
  "type": "session.end"
}
```
**Description:** End the practice session early (before all questions are answered). Triggers report generation.

---

**3.7.5 Ping (Keep-Alive)**
```json
{
  "type": "ping"
}
```
**Description:** Keep WebSocket connection alive. Server responds with `pong`.

---

### Server → Client Events

**3.7.6 Connection Established**
```json
{
  "type": "connection.established",
  "data": {
    "session_id": "uuid",
    "user_id": "uuid",
    "job_role": {
      "id": "uuid",
      "title": "Senior Backend Developer"
    },
    "duration_minutes": 30,
    "num_questions": 5
  }
}
```
**When:** Immediately after WebSocket connection is established
**Next Step:** Client should send `session.start` event

---

**3.7.7 Session Started**
```json
{
  "type": "session.started",
  "data": {
    "started_at": "2024-01-15T10:00:00Z",
    "message": "Practice session started. Generating your first question..."
  }
}
```
**When:** After client sends `session.start`
**Next:** First question will arrive shortly via `question.asked` event

---

**3.7.8 Question Asked**
```json
{
  "type": "question.asked",
  "data": {
    "question_id": "uuid",
    "question_number": 1,
    "question_text": "Can you explain the difference between REST and GraphQL APIs? What are the use cases for each?",
    "question_category": "technical",
    "question_context": "Assessing understanding of API design patterns",
    "expected_topics": [
      "REST principles",
      "GraphQL advantages",
      "Use cases and trade-offs",
      "Performance considerations"
    ],
    "question_audio_url": "https://minio.../question_1.mp3",
    "asked_at": "2024-01-15T10:01:23Z",
    "time_remaining_seconds": 1677
  }
}
```
**When:**
- After session starts (first question)
- After submitting an answer (next question)
**Next Step:** User should answer via `answer.submit` or `answer.audio_chunk` events

---

**3.7.9 Transcription Interim (Real-time)**
```json
{
  "type": "transcription.interim",
  "data": {
    "text": "REST uses HTTP methods and resources to perform CRUD operations",
    "is_final": false,
    "confidence": 0.92,
    "words_per_minute": 145
  }
}
```
**When:** While processing audio chunks (if using `answer.audio_chunk`)
**Purpose:** Show live transcription to user as they speak

---

**3.7.10 Answer Feedback**
```json
{
  "type": "answer.feedback",
  "data": {
    "question_id": "uuid",
    "feedback_id": "uuid",

    "overall_score": 82.5,
    "technical_score": 85.0,
    "communication_score": 80.0,
    "behavioral_score": 83.0,
    "mindset_score": 82.0,

    "technical_metrics": {
      "relevance": 88.0,
      "completeness": 82.0,
      "accuracy": 90.0,
      "depth": 80.0
    },

    "communication_metrics": {
      "fluency": 85.0,
      "grammar": 88.0,
      "vocabulary": 78.0,
      "pronunciation": 82.0,
      "articulation": 80.0,
      "pace": 75.0,
      "tone": 77.0
    },

    "speaking_analysis": {
      "duration_seconds": 87,
      "words_per_minute": 152,
      "filler_words_count": 3,
      "filler_words": ["um", "uh", "like"],
      "pauses_count": 5,
      "average_pause_duration": 1.2
    },

    "ai_feedback_text": "Excellent explanation of REST and GraphQL! You clearly articulated the key differences and use cases. Your understanding of REST principles is strong. To improve, consider elaborating more on GraphQL subscriptions and real-time capabilities.",

    "key_strengths": [
      "Clear explanation of REST principles",
      "Good real-world examples",
      "Well-structured response"
    ],

    "quick_improvements": [
      "Reduce filler words (used 'um' 2 times)",
      "Slow down slightly - you spoke at 152 WPM (ideal: 130-150)",
      "Mention GraphQL subscriptions for real-time use cases"
    ],

    "answer_transcript": "REST uses HTTP methods and resources to perform CRUD operations. It's stateless and cacheable. GraphQL on the other hand allows clients to request exactly what they need...",

    "generated_at": "2024-01-15T10:03:45Z"
  }
}
```
**When:** Immediately after server processes your answer
**Next:** Server automatically sends next question via `question.asked` (or `session.complete` if last question)

---

**3.7.11 Session Complete**
```json
{
  "type": "session.complete",
  "data": {
    "ended_at": "2024-01-15T10:32:18Z",
    "actual_duration": 32,
    "questions_answered": 5,
    "overall_session_score": 79.5,

    "quick_summary": {
      "technical_avg": 81.5,
      "communication_avg": 77.0,
      "behavioral_avg": 80.0,
      "mindset_avg": 79.5,
      "total_filler_words": 23,
      "avg_words_per_minute": 145
    },

    "message": "Great job! You've completed your practice session. Your detailed report is being generated.",
    "report_ready": false,
    "report_url": "/api/v1/practice-sessions/uuid/report/"
  }
}
```
**When:** After answering all questions or sending `session.end` event
**Next Step:** Close WebSocket connection and fetch full report via REST API

---

**3.7.12 Error**
```json
{
  "type": "error",
  "data": {
    "error_code": "invalid_event",
    "message": "Cannot submit answer: no active question",
    "details": {
      "received_event": "answer.submit",
      "session_status": "completed"
    },
    "timestamp": "2024-01-15T10:35:00Z"
  }
}
```
**When:** If client sends invalid event or encounters error
**Common Errors:**
- `invalid_event` - Unknown event type
- `session_not_started` - Trying to submit answer before starting
- `no_active_question` - No question to answer
- `session_expired` - Session exceeded time limit
- `audio_processing_error` - Failed to process audio

---

**3.7.13 Pong (Keep-Alive Response)**
```json
{
  "type": "pong",
  "data": {
    "timestamp": "2024-01-15T10:15:00Z"
  }
}
```
**When:** Response to client's `ping` event

---

## 4. Live Interview APIs (Two-Person)

### 4.1 List Live Interviews
**Endpoint:** `GET /api/v1/live-interviews/`

**Permission:** `IsAuthenticated`

**Query Parameters:**
- `page`, `page_size`: Pagination
- `status`: Filter by status
- `role`: Filter by user's role (interviewer/candidate)
- `scheduled_after`: Filter interviews scheduled after date
- `scheduled_before`: Filter interviews scheduled before date

**Description:** List live interviews (as interviewer or candidate)

**Response:**
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "interviewer": {
        "id": "uuid",
        "username": "jane_interviewer",
        "full_name": "Jane Smith"
      },
      "candidate": {
        "id": "uuid",
        "username": "john_candidate",
        "full_name": "John Doe"
      },
      "job_role": {
        "id": "uuid",
        "title": "Senior Backend Developer"
      },
      "status": "scheduled",
      "enable_realtime_feedback": true,
      "feedback_visibility": "interviewer_only",
      "duration_minutes": 45,
      "room_id": "interview_uuid_12345",
      "scheduled_at": "2024-01-20T14:00:00Z",
      "created_at": "2024-01-15T12:00:00Z"
    }
  ]
}
```

---

### 4.2 Schedule Live Interview
**Endpoint:** `POST /api/v1/live-interviews/`

**Permission:** `CanScheduleLiveInterview` (interviewers and org admins)

**Description:** Schedule a new live interview session

**Request Body:**
```json
{
  "candidate": "uuid",
  "job_role": "uuid",
  "scheduled_at": "2024-01-20T14:00:00Z",
  "duration_minutes": 45,
  "enable_realtime_feedback": true,
  "feedback_visibility": "interviewer_only"
}
```

**Response:**
```json
{
  "id": "uuid",
  "interviewer": "uuid",
  "candidate": "uuid",
  "job_role": "uuid",
  "status": "scheduled",
  "enable_realtime_feedback": true,
  "feedback_visibility": "interviewer_only",
  "duration_minutes": 45,
  "room_id": "interview_uuid_12345",
  "scheduled_at": "2024-01-20T14:00:00Z",
  "websocket_url": "wss://.../ws/interviews/uuid/?token=<jwt>",
  "created_at": "2024-01-15T12:00:00Z"
}
```

---

### 4.3 Get Live Interview Details
**Endpoint:** `GET /api/v1/live-interviews/{id}/`

**Permission:** `IsOwnerOrInterviewer` (interviewer or candidate of the session)

**Description:** Get detailed information about a live interview

**Response:**
```json
{
  "id": "uuid",
  "interviewer": {
    "id": "uuid",
    "username": "jane_interviewer",
    "full_name": "Jane Smith",
    "avatar_url": "https://minio.../avatar.jpg"
  },
  "candidate": {
    "id": "uuid",
    "username": "john_candidate",
    "full_name": "John Doe",
    "avatar_url": "https://minio.../avatar.jpg"
  },
  "job_role": {
    "id": "uuid",
    "title": "Senior Backend Developer",
    "experience_level": "senior"
  },
  "status": "in_progress",
  "enable_realtime_feedback": true,
  "feedback_visibility": "interviewer_only",
  "duration_minutes": 45,
  "room_id": "interview_uuid_12345",
  "scheduled_at": "2024-01-20T14:00:00Z",
  "started_at": "2024-01-20T14:02:00Z",
  "ended_at": null,
  "actual_duration": null,
  "interviewer_notes": "",
  "websocket_url": "wss://.../ws/interviews/uuid/?token=<jwt>",
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-20T14:02:00Z"
}
```

---

### 4.4 Update Live Interview
**Endpoint:** `PUT /api/v1/live-interviews/{id}/`

**Permission:** `IsInterviewerForLiveSession` (interviewer of the session)

**Description:** Update interview details (before it starts)

**Request Body:**
```json
{
  "scheduled_at": "2024-01-20T15:00:00Z",
  "duration_minutes": 60,
  "enable_realtime_feedback": false
}
```

**Response:** Updated interview object

---

### 4.5 Cancel Live Interview
**Endpoint:** `DELETE /api/v1/live-interviews/{id}/`

**Permission:** `IsInterviewerForLiveSession` or `IsOrgAdmin` (interviewer or org admin)

**Description:** Cancel a scheduled live interview

**Response:**
```json
{
  "message": "Live interview cancelled successfully"
}
```

---

### 4.6 Start Live Interview
**Endpoint:** `POST /api/v1/live-interviews/{id}/start/`

**Permission:** `IsInterviewerForLiveSession` (interviewer of the session)

**Description:** Start the live interview session

**Response:**
```json
{
  "id": "uuid",
  "status": "in_progress",
  "started_at": "2024-01-20T14:02:00Z",
  "websocket_url": "wss://.../ws/interviews/uuid/?token=<jwt>",
  "message": "Live interview started. Both parties should connect via WebSocket."
}
```

---

### 4.7 End Live Interview
**Endpoint:** `POST /api/v1/live-interviews/{id}/end/`

**Permission:** `IsInterviewerForLiveSession` (interviewer of the session)

**Description:** End the live interview (triggers report generation for both parties)

**Request Body:**
```json
{
  "interviewer_notes": "Candidate showed strong system design skills...",
  "hiring_recommendation": "yes"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "ended_at": "2024-01-20T14:50:00Z",
  "actual_duration": 48,
  "message": "Live interview ended. Reports are being generated.",
  "reports_ready": false
}
```

---

### 4.8 Get Interviewer Report
**Endpoint:** `GET /api/v1/live-interviews/{id}/reports/interviewer/`

**Permission:** `IsInterviewerForLiveSession` or `IsOrgAdmin` (interviewer of the session or org admin)

**Description:** Get the interviewer's report with hiring recommendation

**Response:**
```json
{
  "id": "uuid",
  "live_session": "uuid",
  "report_type": "interviewer",
  "overall_score": 82.5,
  "technical_score": 85.0,
  "communication_score": 80.0,
  "behavioral_score": 83.0,
  "mindset_score": 82.0,

  "summary": "Strong candidate with excellent system design knowledge...",

  "key_strengths": [
    "Deep understanding of distributed systems",
    "Clear communication of complex concepts",
    "Good problem-solving approach"
  ],

  "areas_for_improvement": [
    "Could improve knowledge of specific AWS services",
    "Practice explaining trade-offs more concisely"
  ],

  "recommendations": [
    "Strong hire for senior backend role",
    "Consider for tech lead track",
    "May need some mentoring on cloud-native patterns"
  ],

  "hiring_recommendation": "yes",
  "interviewer_comments": "Candidate showed strong system design skills...",

  "report_pdf_url": "https://minio.../reports/interviewer_uuid.pdf",
  "generated_at": "2024-01-20T14:55:00Z"
}
```

---

### 4.9 Get Candidate Report
**Endpoint:** `GET /api/v1/live-interviews/{id}/reports/candidate/`

**Permission:** `IsOwnerOrInterviewer` or `IsOrgAdmin` (candidate of the session or org admin)

**Description:** Get the candidate's report (no hiring recommendation)

**Response:**
```json
{
  "id": "uuid",
  "live_session": "uuid",
  "report_type": "candidate",
  "overall_score": 82.5,
  "technical_score": 85.0,
  "communication_score": 80.0,
  "behavioral_score": 83.0,
  "mindset_score": 82.0,

  "summary": "You demonstrated strong technical knowledge...",

  "key_strengths": [
    "Deep understanding of distributed systems",
    "Clear communication of complex concepts",
    "Good problem-solving approach"
  ],

  "areas_for_improvement": [
    "Could improve knowledge of specific AWS services",
    "Practice explaining trade-offs more concisely"
  ],

  "recommendations": [
    "Study AWS services in depth",
    "Practice STAR method for behavioral questions",
    "Continue building distributed systems projects"
  ],

  "report_pdf_url": "https://minio.../reports/candidate_uuid.pdf",
  "generated_at": "2024-01-20T14:55:00Z"
}
```

---

## 5. Progress & Analytics APIs

### 5.1 Get User Progress
**Endpoint:** `GET /api/v1/progress/me/`

**Permission:** `CanViewAnalytics` (own progress only)

**Description:** Get current user's overall progress and statistics

**Response:**
```json
{
  "id": "uuid",
  "user": "uuid",

  "lifetime_stats": {
    "total_sessions": 15,
    "total_questions_answered": 75,
    "total_practice_time": 450
  },

  "score_overview": {
    "average_score": 78.5,
    "highest_score": 92.0,
    "lowest_score": 65.0,
    "recent_scores": [78.5, 82.0, 75.0, 85.0, 79.0],
    "score_trend": "improving"
  },

  "skill_breakdown": {
    "technical_avg": 80.5,
    "communication_avg": 76.0,
    "behavioral_avg": 79.0,
    "mindset_avg": 78.0
  },

  "speaking_patterns": {
    "avg_words_per_minute": 145,
    "total_filler_words": 234,
    "common_filler_words": {
      "um": 89,
      "uh": 67,
      "like": 45,
      "you know": 33
    }
  },

  "category_performance": {
    "strong_categories": ["technical", "mindset"],
    "weak_categories": ["communication"],
    "category_scores": {
      "technical": 80.5,
      "behavioral": 79.0,
      "situational": 77.0,
      "general": 75.0
    }
  },

  "job_role_performance": {
    "practiced_roles": [
      {
        "role_id": "uuid",
        "role_title": "Senior Backend Developer",
        "sessions": 8,
        "avg_score": 82.0
      },
      {
        "role_id": "uuid",
        "role_title": "Full Stack Engineer",
        "sessions": 7,
        "avg_score": 75.0
      }
    ],
    "best_performing_role": "uuid"
  },

  "engagement": {
    "current_streak": 5,
    "longest_streak": 12,
    "last_practice_date": "2024-01-15",
    "weekly_goal": 3,
    "weekly_progress": 2
  },

  "achievements": [
    "first_session",
    "10_sessions",
    "5_day_streak",
    "80_score"
  ],

  "updated_at": "2024-01-15T10:35:00Z"
}
```

---

### 5.2 Get Detailed Statistics
**Endpoint:** `GET /api/v1/progress/me/stats/`

**Permission:** `CanViewAnalytics`

**Description:** Get granular statistics and breakdowns

**Response:**
```json
{
  "technical_details": {
    "technical_avg": 80.5,
    "technical_history": [78.0, 80.0, 82.0, 81.0, 85.0, 80.0, 79.0, 83.0, 82.0, 80.5],
    "strongest_technical_areas": ["system design", "algorithms", "databases"],
    "weakest_technical_areas": ["security", "networking"]
  },

  "communication_details": {
    "communication_avg": 76.0,
    "communication_history": [72.0, 74.0, 76.0, 75.0, 78.0, 76.0, 77.0, 79.0, 75.0, 76.0],
    "fluency_avg": 78.0,
    "grammar_avg": 82.0,
    "vocabulary_avg": 74.0,
    "pronunciation_avg": 76.0
  },

  "behavioral_details": {
    "behavioral_avg": 79.0,
    "behavioral_history": [75.0, 77.0, 79.0, 80.0, 82.0, 78.0, 79.0, 81.0, 80.0, 79.0],
    "confidence_avg": 80.0,
    "professionalism_avg": 82.0,
    "enthusiasm_avg": 76.0
  },

  "mindset_details": {
    "mindset_avg": 78.0,
    "mindset_history": [74.0, 76.0, 78.0, 79.0, 80.0, 78.0, 77.0, 79.0, 81.0, 78.0],
    "critical_thinking_avg": 79.0,
    "structure_avg": 77.0,
    "growth_mindset_avg": 78.0
  },

  "filler_word_analysis": {
    "total_filler_words": 234,
    "filler_word_trend": [35, 32, 28, 25, 23, 22, 20, 18, 17, 14],
    "common_filler_words": {
      "um": 89,
      "uh": 67,
      "like": 45,
      "you know": 33
    }
  }
}
```

---

### 5.3 Get Score Trends
**Endpoint:** `GET /api/v1/progress/me/trends/`

**Permission:** `CanViewAnalytics`

**Query Parameters:**
- `period`: Time period (7d, 30d, 90d, all)
- `metric`: Specific metric to trend (overall, technical, communication, etc.)

**Description:** Get score trends over time

**Response:**
```json
{
  "period": "30d",
  "data_points": [
    {
      "date": "2024-01-01",
      "overall_score": 75.0,
      "technical_score": 78.0,
      "communication_score": 72.0,
      "behavioral_score": 76.0,
      "mindset_score": 74.0,
      "session_count": 1
    },
    {
      "date": "2024-01-08",
      "overall_score": 78.5,
      "technical_score": 80.5,
      "communication_score": 76.0,
      "behavioral_score": 79.0,
      "mindset_score": 78.0,
      "session_count": 2
    }
  ],
  "trend_analysis": {
    "overall_trend": "improving",
    "improvement_rate": 1.2,
    "best_week": "2024-01-08",
    "worst_week": "2024-01-01"
  }
}
```

---

### 5.4 Get Achievements
**Endpoint:** `GET /api/v1/progress/me/achievements/`

**Permission:** `CanViewAnalytics`

**Description:** Get list of unlocked achievements and progress toward next ones

**Response:**
```json
{
  "unlocked_achievements": [
    {
      "name": "first_session",
      "title": "First Steps",
      "description": "Complete your first practice session",
      "icon": "🎯",
      "unlocked_at": "2024-01-01T10:35:00Z"
    },
    {
      "name": "10_sessions",
      "title": "Committed Learner",
      "description": "Complete 10 practice sessions",
      "icon": "📚",
      "unlocked_at": "2024-01-10T14:20:00Z"
    },
    {
      "name": "5_day_streak",
      "title": "On Fire",
      "description": "Practice for 5 consecutive days",
      "icon": "🔥",
      "unlocked_at": "2024-01-12T09:15:00Z"
    }
  ],

  "progress_toward_next": [
    {
      "name": "50_sessions",
      "title": "Interview Master",
      "description": "Complete 50 practice sessions",
      "icon": "🏆",
      "progress": 15,
      "target": 50,
      "percentage": 30.0
    },
    {
      "name": "90_score",
      "title": "Excellence",
      "description": "Achieve a score of 90 or higher",
      "icon": "⭐",
      "progress": 92.0,
      "target": 90.0,
      "percentage": 100.0,
      "ready_to_unlock": true
    }
  ]
}
```

---

### 5.5 Get Analytics (Admin)
**Endpoint:** `GET /api/v1/analytics/sessions/`

**Permission:** `IsOrgAdmin` (organization admins only)

**Query Parameters:**
- `start_date`, `end_date`: Date range
- `user_id`: Filter by user
- `job_role`: Filter by job role

**Description:** Get aggregated session analytics (admin only)

**Response:**
```json
{
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },

  "overview": {
    "total_sessions": 234,
    "total_users": 45,
    "average_score": 78.2,
    "completion_rate": 0.87
  },

  "score_distribution": {
    "0-50": 5,
    "50-60": 12,
    "60-70": 38,
    "70-80": 87,
    "80-90": 78,
    "90-100": 14
  },

  "popular_job_roles": [
    {
      "job_role_id": "uuid",
      "job_role_title": "Senior Backend Developer",
      "session_count": 89,
      "average_score": 79.5
    }
  ],

  "user_engagement": {
    "active_users_7d": 32,
    "active_users_30d": 45,
    "average_sessions_per_user": 5.2,
    "average_streak": 3.5
  }
}
```

---

## 6. AI/Speech Provider Management APIs (Admin)

### 6.1 List AI Providers
**Endpoint:** `GET /api/v1/admin/ai-providers/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** List all configured AI/LLM providers

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "name": "OpenAI GPT-3.5",
      "provider_type": "openai",
      "model_name": "gpt-3.5-turbo",
      "supports_question_generation": true,
      "supports_feedback_analysis": true,
      "supports_transcription": false,
      "temperature": 0.7,
      "max_tokens": 2000,
      "is_active": true,
      "is_default": true,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "name": "Anthropic Claude",
      "provider_type": "anthropic",
      "model_name": "claude-3-sonnet-20240229",
      "supports_question_generation": true,
      "supports_feedback_analysis": true,
      "supports_transcription": false,
      "temperature": 0.7,
      "max_tokens": 2000,
      "is_active": true,
      "is_default": false,
      "created_at": "2024-01-05T00:00:00Z"
    }
  ]
}
```

---

### 6.2 Add AI Provider
**Endpoint:** `POST /api/v1/admin/ai-providers/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** Add a new AI provider configuration

**Request Body:**
```json
{
  "name": "OpenAI GPT-4",
  "provider_type": "openai",
  "api_key": "sk-...",
  "model_name": "gpt-4-turbo-preview",
  "base_url": "",
  "supports_question_generation": true,
  "supports_feedback_analysis": true,
  "supports_transcription": false,
  "temperature": 0.7,
  "max_tokens": 4000,
  "additional_config": {}
}
```

**Response:** Created provider object (API key is encrypted in storage)

---

### 6.3 Update AI Provider
**Endpoint:** `PUT /api/v1/admin/ai-providers/{id}/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** Update AI provider configuration

**Request Body:** Same as 6.2

**Response:** Updated provider object

---

### 6.4 Delete AI Provider
**Endpoint:** `DELETE /api/v1/admin/ai-providers/{id}/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** Delete an AI provider

**Response:**
```json
{
  "message": "AI provider deleted successfully"
}
```

---

### 6.5 Set Default AI Provider
**Endpoint:** `POST /api/v1/admin/ai-providers/{id}/set-default/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** Set provider as default for all operations

**Response:**
```json
{
  "message": "Default AI provider updated",
  "provider_id": "uuid",
  "provider_name": "OpenAI GPT-4"
}
```

---

### 6.6 List Speech Providers
**Endpoint:** `GET /api/v1/admin/speech-providers/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** List all configured speech providers

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": "uuid",
      "name": "OpenAI Whisper Local",
      "provider_type": "openai_whisper",
      "service_type": "stt",
      "language_support": ["en", "es", "fr", "de"],
      "is_active": true,
      "is_default_stt": true,
      "is_default_tts": false,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "name": "OpenAI TTS",
      "provider_type": "openai_whisper",
      "service_type": "tts",
      "language_support": ["en"],
      "is_active": true,
      "is_default_stt": false,
      "is_default_tts": true,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "name": "AssemblyAI Realtime",
      "provider_type": "assemblyai",
      "service_type": "stt",
      "language_support": ["en"],
      "is_active": true,
      "is_default_stt": false,
      "is_default_tts": false,
      "created_at": "2024-01-05T00:00:00Z"
    }
  ]
}
```

---

### 6.7 Add Speech Provider
**Endpoint:** `POST /api/v1/admin/speech-providers/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** Add a new speech provider

**Request Body:**
```json
{
  "name": "AssemblyAI Realtime",
  "provider_type": "assemblyai",
  "service_type": "stt",
  "api_key": "...",
  "base_url": "",
  "language_support": ["en"],
  "additional_config": {
    "real_time": true
  }
}
```

**Response:** Created provider object

---

### 6.8 Update Speech Provider
**Endpoint:** `PUT /api/v1/admin/speech-providers/{id}/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** Update speech provider configuration

**Request Body:** Same as 6.7

**Response:** Updated provider object

---

### 6.9 Delete Speech Provider
**Endpoint:** `DELETE /api/v1/admin/speech-providers/{id}/`

**Permission:** `CanManageAIProviders` (organization admins only)

**Description:** Delete a speech provider

**Response:**
```json
{
  "message": "Speech provider deleted successfully"
}
```

---

## 7. WebSocket API

### 7.1 Practice Session WebSocket
**Endpoint:** `WS /ws/practice-sessions/{session_id}/`

**See Section 3.7** for complete documentation of the Practice Session WebSocket API, including:
- Connection flow
- Client → Server events (session.start, answer.submit, answer.audio_chunk, session.end, ping)
- Server → Client events (connection.established, session.started, question.asked, transcription.interim, answer.feedback, session.complete, error, pong)
- Complete JavaScript example code

---

### 7.2 Live Interview WebSocket Connection
**Endpoint:** `WS /ws/interviews/{session_id}/`

**Authentication:** JWT token in query parameter

**Connection URL:**
```
wss://your-domain.com/ws/interviews/{session_id}/?token=<jwt_token>
```

**Description:** Real-time bidirectional communication for live interviews between interviewer and candidate

---

#### Connection Events

**7.2.1 Connection Established (Server → Client)**
```json
{
  "type": "connection.established",
  "data": {
    "session_id": "uuid",
    "user_id": "uuid",
    "user_role": "interviewer"
  }
}
```

---

#### Interview Lifecycle Events

**7.2.2 Interview Started (Server → Both)**
```json
{
  "type": "interview.started",
  "data": {
    "started_at": "2024-01-20T14:02:00Z",
    "duration_minutes": 45
  }
}
```

**7.2.3 Interview Ended (Server → Both)**
```json
{
  "type": "interview.ended",
  "data": {
    "ended_at": "2024-01-20T14:50:00Z",
    "total_questions": 8
  }
}
```

---

#### Question Events

**7.2.4 Question Asked (Server → Both)**
```json
{
  "type": "question.asked",
  "data": {
    "question_id": "uuid",
    "question_number": 1,
    "question_text": "Explain the CAP theorem",
    "question_category": "technical",
    "question_audio_url": "https://minio.../question.mp3"
  }
}
```

**7.2.5 Ask Question (Client → Server)** *(Phase 4)*
```json
{
  "type": "question.ask",
  "data": {
    "question_text": "Can you explain your approach to testing?",
    "is_ai_generated": false
  }
}
```

---

#### Audio Events

**7.2.6 Audio Chunk (Client → Server)** *(Phase 4)*
```json
{
  "type": "audio.chunk",
  "data": {
    "chunk": "<base64_encoded_audio>",
    "sequence": 123,
    "is_final": false
  }
}
```

**7.2.7 Transcription Interim (Server → Both)** *(Phase 4)*
```json
{
  "type": "transcription.interim",
  "data": {
    "text": "The CAP theorem states that...",
    "is_final": false,
    "speaker": "candidate"
  }
}
```

---

#### Feedback Events

**7.2.8 Real-time Feedback (Server → Interviewer Only)** *(Phase 4)*
```json
{
  "type": "feedback.realtime",
  "data": {
    "question_id": "uuid",
    "scores": {
      "relevance": 85,
      "completeness": 78,
      "confidence": 82
    },
    "insights": [
      "Good understanding of distributed systems",
      "Could elaborate on consistency models"
    ],
    "suggested_followup": "Can you explain eventual consistency?"
  }
}
```

---

#### Answer Events

**7.2.9 Answer Submitted (Server → Both)**
```json
{
  "type": "answer.submitted",
  "data": {
    "question_id": "uuid",
    "transcript": "The CAP theorem states...",
    "duration_seconds": 145
  }
}
```

---

## 8. Health & Utility APIs

### 8.1 Health Check
**Endpoint:** `GET /api/v1/health/`

**Permission:** `AllowAny` (no authentication required)

**Description:** Check service health status

**Response:**
```json
{
  "status": "healthy",
  "service": "interview_service",
  "version": "1.0.0",
  "timestamp": "2024-01-15T12:00:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "kafka": "healthy",
    "minio": "healthy",
    "celery": "healthy"
  }
}
```

---

### 8.2 API Schema (OpenAPI)
**Endpoint:** `GET /api/schema/`

**Permission:** `AllowAny`

**Description:** Get OpenAPI 3.0 schema in JSON format

**Response:** OpenAPI schema JSON

---

### 8.3 Swagger UI
**Endpoint:** `GET /api/schema/swagger-ui/`

**Permission:** `AllowAny`

**Description:** Interactive API documentation (Swagger UI)

**Response:** HTML page with Swagger UI

---

### 8.4 ReDoc
**Endpoint:** `GET /api/schema/redoc/`

**Permission:** `AllowAny`

**Description:** Alternative API documentation (ReDoc)

**Response:** HTML page with ReDoc UI

---

### 8.5 Test Permission Endpoint (Testing Only)
**Endpoint:** `GET /api/v1/test-permission/`

**Permission:** `IsTestUser` (allows all access - for testing only)

**Description:** Test endpoint to verify the IsTestUser permission class is working correctly. This endpoint is accessible without authentication.

**⚠️ WARNING:** This endpoint uses `IsTestUser` permission which allows unrestricted access. Remove this endpoint and permission class in production!

**Response:**
```json
{
  "message": "Success! IsTestUser permission is working.",
  "description": "This endpoint uses IsTestUser permission class which allows all access.",
  "user_authenticated": false,
  "user": "Anonymous",
  "note": "This permission class should only be used for testing. Remove it in production!"
}
```

**Usage Example:**
```bash
# No authentication required
curl http://localhost:8000/api/v1/test-permission/

# Even with invalid token, it still works
curl -H "Authorization: Bearer invalid_token" http://localhost:8000/api/v1/test-permission/
```

---

## Common Response Codes

### Success Codes
- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `204 No Content` - Request succeeded, no response body

### Client Error Codes
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Authenticated but not authorized
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded

### Server Error Codes
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - Upstream service error
- `503 Service Unavailable` - Service temporarily unavailable

---

## Error Response Format

All error responses follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": ["Error message for specific field"]
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

**Example:**
```json
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "email": ["This field is required"],
    "num_questions": ["Ensure this value is greater than or equal to 1"]
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

---

## Pagination

List endpoints support pagination with these parameters:

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20, max: 100)

**Response Format:**
```json
{
  "count": 150,
  "next": "https://.../api/v1/resource/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Sorting

Many list endpoints support filtering and sorting:

**Common Query Parameters:**
- `ordering`: Sort by field (prefix with `-` for descending, e.g., `-created_at`)
- `search`: Search across multiple fields
- Model-specific filters (see individual endpoint documentation)

**Example:**
```
GET /api/v1/practice-sessions/?status=completed&ordering=-created_at&page=1&page_size=10
```

---

## File Upload Constraints

### Avatar Upload
- **Formats:** JPEG, PNG, GIF
- **Max Size:** 5 MB
- **Recommended:** 512x512 pixels

### Resume Upload
- **Format:** PDF only
- **Max Size:** 2 MB

### Audio Upload
- **Formats:** MP3, WAV, OGG, WebM
- **Max Size:** 10 MB per file
- **Recommended:** MP3 @ 128kbps or higher

---

## Rate Limiting

**Anonymous Users:** 100 requests/hour
**Authenticated Users:** 1000 requests/hour

Rate limit headers in response:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705329600
```

---

## Summary of Endpoints

### Total Endpoints: 32 REST + 2 WebSocket

**By Category:**
- Authentication & Profile: 8 REST endpoints
- Job Roles: 5 REST endpoints
- Practice Sessions: 6 REST endpoints + 1 WebSocket endpoint (conversational)
- Live Interviews: 9 REST endpoints + 1 WebSocket endpoint
- Progress & Analytics: 5 REST endpoints
- Provider Management: 9 REST endpoints (admin)
- Health & Utility: 4 REST endpoints

**Architecture Overview:**
- **REST APIs:** Session management, CRUD operations, reports, analytics
- **WebSocket APIs:** Real-time conversational flows (practice sessions + live interviews)

**Practice Session Flow:**
1. Create session via REST → Get WebSocket URL
2. Connect to WebSocket → Start conversational flow
3. Entire Q&A happens over WebSocket (low latency, natural flow)
4. Fetch report via REST after completion

**By Priority (Implementation Order):**
1. **Phase 1 (Foundation):** Authentication, Profile, Job Roles, Health
2. **Phase 2 (Solo Practice MVP):** Practice Sessions REST + WebSocket, Progress
3. **Phase 3 (Audio):** File uploads, Audio processing, Real-time transcription
4. **Phase 4 (Live Interviews):** Live interview REST + WebSocket endpoints
5. **Phase 5 (Advanced):** Provider management, Analytics

---

## Next Steps for Implementation

1. **Create DRF Serializers** for all 12 models in `interviews/serializers.py`
2. **Create ViewSets** for REST endpoints in `interviews/views.py`
3. **Configure URL routing** in `interviews/urls.py` and `interview_service/urls.py`
4. **Implement WebSocket Consumers:**
   - `PracticeSessionConsumer` in `interviews/consumers.py` for practice sessions
   - Enhance `InterviewConsumer` for live interviews
5. **Create Celery tasks** for async operations:
   - AI question generation (ai_queue)
   - Answer feedback analysis (ai_queue)
   - Report generation (ai_queue)
   - Audio processing & transcription (audio_queue)
   - Progress tracking (interview_queue)
6. **Implement file upload handlers** for MinIO integration (avatar, resume, audio)
7. **Add WebSocket event handlers** for each message type (session.start, answer.submit, etc.)
8. **Test REST endpoints** with Swagger UI
9. **Test WebSocket flows** with WebSocket client tools
10. **Add validation logic** and comprehensive error handling

**Key Implementation Notes:**
- Practice session conversation flow is entirely WebSocket-based (not REST)
- REST APIs for practice sessions only handle: create, list, get details, get report, cancel
- WebSocket provides natural, low-latency conversational experience
- Use Django Channels groups for broadcasting to multiple clients (live interviews)

Good luck with the implementation! 🚀
