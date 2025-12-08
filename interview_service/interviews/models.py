import uuid
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """
    Synced from auth_service via Kafka events.
    Basic fields are created via event, extended fields updated via API.
    """
    ROLE_CHOICES = [
        ("organization_admin", "Organization Admin"),
        ("interviewer", "Interviewer"),
        ("candidate", "Candidate"),
    ]

    # === Fields synced from auth_service (via Kafka) ===
    id = models.UUIDField(primary_key=True, editable=False)  # Same as auth_service user.id
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # === Interview-specific profile fields (updated via API) ===
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)  # Stored in MinIO
    resume_url = models.URLField(max_length=500, blank=True)  # Stored in MinIO
    
    # === Professional info ===
    current_job_title = models.CharField(max_length=150, blank=True)
    current_company = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    skills = models.JSONField(default=list, blank=True)  # ["python", "django", "aws"]
    linkedin_url = models.URLField(max_length=500, blank=True)
    github_url = models.URLField(max_length=500, blank=True)
    portfolio_url = models.URLField(max_length=500, blank=True)
    
    # === Preferences ===
    preferred_language = models.CharField(max_length=10, default="en")  # For TTS/STT
    user_timezone = models.CharField(max_length=50, default="UTC")
    email_notifications = models.BooleanField(default=True)
    
    # === Metadata ===
    auth_synced_at = models.DateTimeField(auto_now_add=True)  # When synced from auth_service
    profile_updated_at = models.DateTimeField(auto_now=True)  # When profile was updated via API
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_interviewer(self):
        return self.role == "interviewer"

    @property
    def is_candidate(self):
        return self.role == "candidate"

    @property
    def is_org_admin(self):
        return self.role == "organization_admin"

    @property
    def display_name(self):
        return self.full_name or self.username


class JobRole(models.Model):
    """
    Job role context for AI to generate relevant interview questions.
    No predefined questions - AI generates dynamically based on this context.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)  # "Senior Backend Developer"
    description = models.TextField(blank=True)  # Role responsibilities, expectations
    
    # === Context for AI Question Generation ===
    required_skills = models.JSONField(default=list)  # ["python", "system design", "databases"]
    preferred_skills = models.JSONField(default=list)  # Nice-to-have skills
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ("entry", "Entry Level"),
            ("mid", "Mid Level"),
            ("senior", "Senior Level"),
            ("lead", "Lead/Principal"),
        ],
        default="mid"
    )
    industry = models.CharField(max_length=100, blank=True)  # "fintech", "healthcare"
    company_context = models.TextField(blank=True)  # Optional: company culture, team info
    
    # === AI Generation Settings ===
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
            ("mixed", "Mixed"),
        ],
        default="medium"
    )
    # Weightage for question types (AI uses these proportions)
    technical_weight = models.FloatField(default=0.4)  # 40% technical questions
    behavioral_weight = models.FloatField(default=0.3)  # 30% behavioral
    situational_weight = models.FloatField(default=0.2)  # 20% situational
    general_weight = models.FloatField(default=0.1)  # 10% general/intro
    
    # Topics AI should cover
    key_topics = models.JSONField(default=list)  # ["microservices", "team leadership", "agile"]
    topics_to_avoid = models.JSONField(default=list)  # Topics to skip
    
    # Additional AI instructions
    custom_instructions = models.TextField(blank=True)  # Extra context for AI
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["experience_level"]),
            models.Index(fields=["industry"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["difficulty_level"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.experience_level})"
    
    @property
    def question_type_weights(self):
        """Returns weights dict for AI to use when generating questions"""
        return {
            "technical": self.technical_weight,
            "behavioral": self.behavioral_weight,
            "situational": self.situational_weight,
            "general": self.general_weight,
        }


class PracticeSession(models.Model):
    """
    A single practice interview session.
    """
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="practice_sessions")
    job_role = models.ForeignKey(JobRole, on_delete=models.SET_NULL, null=True, related_name="practice_sessions")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    
    # Session configuration
    duration_minutes = models.PositiveIntegerField(default=30)  # Target duration
    num_questions = models.PositiveIntegerField(default=5)
    
    # Timing
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Session recording (stored in MinIO)
    full_audio_url = models.URLField(blank=True)  # Complete session recording
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.job_role.title if self.job_role else 'No role'} ({self.status})"

    @property
    def actual_duration(self):
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).seconds // 60
        return None


class SessionQuestion(models.Model):
    """
    Individual question asked during a practice session.
    Generated by AI based on job role.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name="questions")
    
    # Question details
    question_number = models.PositiveIntegerField()
    question_text = models.TextField()
    question_category = models.CharField(max_length=50)  # "technical", "behavioral", etc.
    
    # AI-generated context (why this question was asked)
    question_context = models.TextField(blank=True)
    expected_topics = models.JSONField(default=list)  # Topics a good answer should cover
    
    # Timing
    asked_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    # Audio storage (MinIO)
    question_audio_url = models.URLField(blank=True)  # TTS audio of question
    answer_audio_url = models.URLField(blank=True)  # User's recorded answer
    
    # Transcription
    answer_transcript = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["question_number"]
        unique_together = ["session", "question_number"]
        indexes = [
            models.Index(fields=["session", "question_number"]),
            models.Index(fields=["question_category"]),
            models.Index(fields=["asked_at"]),
        ]

    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}..."


class QuestionFeedback(models.Model):
    """
    Real-time AI feedback for each answer.
    Generated as user speaks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(SessionQuestion, on_delete=models.CASCADE, related_name="feedback")
    
    # === Technical/Content Analysis ===
    relevance_score = models.FloatField(default=0)  # 0-100: How relevant to the question
    completeness_score = models.FloatField(default=0)  # 0-100: Covered expected topics
    accuracy_score = models.FloatField(default=0)  # 0-100: Technical accuracy
    depth_score = models.FloatField(default=0)  # 0-100: Depth of knowledge shown
    
    # === Language & Communication ===
    fluency_score = models.FloatField(default=0)  # 0-100: Smooth, natural speech flow
    grammar_score = models.FloatField(default=0)  # 0-100: Grammatical correctness
    vocabulary_score = models.FloatField(default=0)  # 0-100: Appropriate word choice
    pronunciation_score = models.FloatField(default=0)  # 0-100: Clear pronunciation
    articulation_score = models.FloatField(default=0)  # 0-100: Clear expression of ideas
    
    # === Speaking Patterns ===
    pace_score = models.FloatField(default=0)  # 0-100: Speaking pace (not too fast/slow)
    tone_score = models.FloatField(default=0)  # 0-100: Professional, engaging tone
    filler_word_count = models.PositiveIntegerField(default=0)
    filler_words_detected = models.JSONField(default=list)  # [{"word": "um", "count": 5}]
    pause_patterns = models.JSONField(default=dict)  # {"long_pauses": 2, "avg_pause_duration": 1.5}
    words_per_minute = models.PositiveIntegerField(default=0)
    
    # === Behavioral & Soft Skills ===
    confidence_score = models.FloatField(default=0)  # 0-100: Confidence in delivery
    enthusiasm_score = models.FloatField(default=0)  # 0-100: Energy and engagement
    professionalism_score = models.FloatField(default=0)  # 0-100: Professional demeanor
    adaptability_score = models.FloatField(default=0)  # 0-100: Handling follow-ups, pivots
    
    # === Mindset & Problem Solving ===
    structure_score = models.FloatField(default=0)  # 0-100: Organized, logical response
    critical_thinking_score = models.FloatField(default=0)  # 0-100: Analytical approach
    creativity_score = models.FloatField(default=0)  # 0-100: Unique perspectives, solutions
    growth_mindset_score = models.FloatField(default=0)  # 0-100: Learning attitude, self-awareness
    
    # === Detailed Feedback ===
    strengths = models.JSONField(default=list)
    improvements = models.JSONField(default=list)
    ai_feedback_text = models.TextField(blank=True)
    
    # Topics analysis
    topics_covered = models.JSONField(default=list)
    topics_missed = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Feedback for Q{self.question.question_number}"

    @property
    def technical_score(self):
        """Average of technical/content scores"""
        scores = [self.relevance_score, self.completeness_score, self.accuracy_score, self.depth_score]
        return sum(scores) / len(scores)

    @property
    def communication_score(self):
        """Average of language and speaking scores"""
        scores = [
            self.fluency_score, self.grammar_score, self.vocabulary_score,
            self.pronunciation_score, self.articulation_score, self.pace_score, self.tone_score
        ]
        return sum(scores) / len(scores)

    @property
    def behavioral_score(self):
        """Average of soft skills scores"""
        scores = [
            self.confidence_score, self.enthusiasm_score,
            self.professionalism_score, self.adaptability_score
        ]
        return sum(scores) / len(scores)

    @property
    def mindset_score(self):
        """Average of mindset/problem-solving scores"""
        scores = [
            self.structure_score, self.critical_thinking_score,
            self.creativity_score, self.growth_mindset_score
        ]
        return sum(scores) / len(scores)

    @property
    def overall_score(self):
        """Weighted overall score"""
        weights = {
            "technical": 0.30,
            "communication": 0.30,
            "behavioral": 0.25,
            "mindset": 0.15,
        }
        return (
            self.technical_score * weights["technical"] +
            self.communication_score * weights["communication"] +
            self.behavioral_score * weights["behavioral"] +
            self.mindset_score * weights["mindset"]
        )


class SessionReport(models.Model):
    """
    Final comprehensive report for a practice session.
    Generated after session ends.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(PracticeSession, on_delete=models.CASCADE, related_name="report")
    
    # === Overall Score ===
    overall_score = models.FloatField(default=0)  # 0-100
    
    # === Technical Scores (aggregated from questions) ===
    technical_score = models.FloatField(default=0)
    relevance_avg = models.FloatField(default=0)
    completeness_avg = models.FloatField(default=0)
    accuracy_avg = models.FloatField(default=0)
    depth_avg = models.FloatField(default=0)
    
    # === Communication Scores ===
    communication_score = models.FloatField(default=0)
    fluency_avg = models.FloatField(default=0)
    grammar_avg = models.FloatField(default=0)
    vocabulary_avg = models.FloatField(default=0)
    pronunciation_avg = models.FloatField(default=0)
    articulation_avg = models.FloatField(default=0)
    pace_avg = models.FloatField(default=0)
    tone_avg = models.FloatField(default=0)
    
    # === Behavioral Scores ===
    behavioral_score = models.FloatField(default=0)
    confidence_avg = models.FloatField(default=0)
    enthusiasm_avg = models.FloatField(default=0)
    professionalism_avg = models.FloatField(default=0)
    adaptability_avg = models.FloatField(default=0)
    
    # === Mindset Scores ===
    mindset_score = models.FloatField(default=0)
    structure_avg = models.FloatField(default=0)
    critical_thinking_avg = models.FloatField(default=0)
    creativity_avg = models.FloatField(default=0)
    growth_mindset_avg = models.FloatField(default=0)
    
    # === Speaking Metrics ===
    total_speaking_time = models.PositiveIntegerField(default=0)  # seconds
    average_response_time = models.FloatField(default=0)  # seconds per question
    total_filler_words = models.PositiveIntegerField(default=0)
    average_words_per_minute = models.PositiveIntegerField(default=0)
    filler_word_breakdown = models.JSONField(default=dict)  # {"um": 10, "uh": 5, "like": 8}
    
    # === AI-generated Insights ===
    summary = models.TextField(blank=True)
    key_strengths = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    
    # Category-wise feedback
    technical_feedback = models.TextField(blank=True)
    communication_feedback = models.TextField(blank=True)
    behavioral_feedback = models.TextField(blank=True)
    mindset_feedback = models.TextField(blank=True)
    
    # === Comparison & Trends ===
    improvement_from_last = models.FloatField(null=True, blank=True)
    score_percentile = models.FloatField(null=True, blank=True)  # Compared to other users
    
    # Report file (PDF stored in MinIO)
    report_pdf_url = models.URLField(blank=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["generated_at"]),
            models.Index(fields=["overall_score"]),
        ]

    def __str__(self):
        return f"Report for {self.session}"


class UserProgress(models.Model):
    """
    Track user's overall progress across all practice sessions.
    Updated after each session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="progress")
    
    # === Lifetime Stats ===
    total_sessions = models.PositiveIntegerField(default=0)
    total_questions_answered = models.PositiveIntegerField(default=0)
    total_practice_time = models.PositiveIntegerField(default=0)  # minutes
    
    # === Overall Score Trends ===
    average_score = models.FloatField(default=0)
    highest_score = models.FloatField(default=0)
    lowest_score = models.FloatField(default=0)
    recent_scores = models.JSONField(default=list)  # Last 10 session scores
    score_trend = models.CharField(
        max_length=20,
        choices=[
            ("improving", "Improving"),
            ("stable", "Stable"),
            ("declining", "Declining"),
        ],
        default="stable"
    )
    
    # === Technical Skills Tracking ===
    technical_avg = models.FloatField(default=0)
    technical_history = models.JSONField(default=list)  # Last 10 scores
    strongest_technical_areas = models.JSONField(default=list)  # ["python", "system design"]
    weakest_technical_areas = models.JSONField(default=list)
    
    # === Communication Skills Tracking ===
    communication_avg = models.FloatField(default=0)
    communication_history = models.JSONField(default=list)
    fluency_avg = models.FloatField(default=0)
    grammar_avg = models.FloatField(default=0)
    vocabulary_avg = models.FloatField(default=0)
    pronunciation_avg = models.FloatField(default=0)
    
    # === Behavioral Skills Tracking ===
    behavioral_avg = models.FloatField(default=0)
    behavioral_history = models.JSONField(default=list)
    confidence_avg = models.FloatField(default=0)
    professionalism_avg = models.FloatField(default=0)
    enthusiasm_avg = models.FloatField(default=0)
    
    # === Mindset Tracking ===
    mindset_avg = models.FloatField(default=0)
    mindset_history = models.JSONField(default=list)
    critical_thinking_avg = models.FloatField(default=0)
    structure_avg = models.FloatField(default=0)
    growth_mindset_avg = models.FloatField(default=0)
    
    # === Speaking Patterns (Lifetime) ===
    avg_words_per_minute = models.PositiveIntegerField(default=0)
    total_filler_words = models.PositiveIntegerField(default=0)
    filler_word_trend = models.JSONField(default=list)  # Track improvement over time
    common_filler_words = models.JSONField(default=dict)  # {"um": 50, "like": 30}
    
    # === Category Performance ===
    strong_categories = models.JSONField(default=list)  # ["behavioral", "technical"]
    weak_categories = models.JSONField(default=list)
    category_scores = models.JSONField(default=dict)  # {"technical": 75, "behavioral": 82}
    
    # === Job Role Performance ===
    practiced_roles = models.JSONField(default=list)  # [{"role_id": "...", "sessions": 5, "avg_score": 78}]
    best_performing_role = models.UUIDField(null=True, blank=True)
    
    # === Streaks and Engagement ===
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_practice_date = models.DateField(null=True, blank=True)
    weekly_goal = models.PositiveIntegerField(default=3)  # Sessions per week target
    weekly_progress = models.PositiveIntegerField(default=0)
    
    # === Achievements/Milestones ===
    achievements = models.JSONField(default=list)  # ["first_session", "10_sessions", "90_score"]
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["average_score"]),
            models.Index(fields=["total_sessions"]),
            models.Index(fields=["last_practice_date"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"Progress: {self.user.username}"


class LiveInterviewSession(models.Model):
    """
    Real-time interview session between interviewer and candidate.
    Supports real-time AI feedback visible only to interviewer (configurable).
    """
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("waiting", "Waiting for Participants"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    FEEDBACK_VISIBILITY_CHOICES = [
        ("interviewer_only", "Interviewer Only"),
        ("both", "Both Parties"),
        ("none", "No Real-time Feedback"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interviewer = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="conducted_interviews"
    )
    candidate = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="live_interviews"
    )
    job_role = models.ForeignKey(
        JobRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="live_interviews"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")

    # Real-time feedback configuration
    enable_realtime_feedback = models.BooleanField(default=True)
    feedback_visibility = models.CharField(
        max_length=20,
        choices=FEEDBACK_VISIBILITY_CHOICES,
        default="interviewer_only"
    )

    # Session configuration
    duration_minutes = models.PositiveIntegerField(default=45)

    # WebSocket room identifier for real-time communication
    room_id = models.CharField(max_length=100, unique=True, db_index=True)

    # Timing
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Recordings (stored in MinIO)
    full_audio_url = models.URLField(max_length=500, blank=True)
    full_video_url = models.URLField(max_length=500, blank=True)

    # Notes during interview
    interviewer_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["interviewer", "status"]),
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.interviewer.username} interviewing {self.candidate.username} ({self.status})"

    @property
    def actual_duration(self):
        """Calculate actual interview duration in minutes"""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).seconds // 60
        return None


class LiveInterviewQuestion(models.Model):
    """
    Questions asked during live interview (AI-generated or custom).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_session = models.ForeignKey(
        LiveInterviewSession,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    # Question details
    question_number = models.PositiveIntegerField()
    question_text = models.TextField()
    question_category = models.CharField(max_length=50)

    # Source tracking
    is_ai_generated = models.BooleanField(default=True)
    custom_question = models.BooleanField(default=False)

    # AI context
    expected_topics = models.JSONField(default=list)

    # Timing
    asked_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    # Audio segments (stored in MinIO)
    question_audio_url = models.URLField(max_length=500, blank=True)
    answer_audio_url = models.URLField(max_length=500, blank=True)
    answer_transcript = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["question_number"]
        unique_together = ["live_session", "question_number"]
        indexes = [
            models.Index(fields=["live_session", "question_number"]),
            models.Index(fields=["question_category"]),
            models.Index(fields=["asked_at"]),
        ]

    def __str__(self):
        return f"Live Q{self.question_number}: {self.question_text[:50]}..."


class LiveInterviewReport(models.Model):
    """
    Separate reports for interviewer and candidate after live interview.
    """
    REPORT_TYPE_CHOICES = [
        ("interviewer", "Interviewer Report"),
        ("candidate", "Candidate Report"),
    ]

    HIRING_RECOMMENDATION_CHOICES = [
        ("strong_yes", "Strong Yes"),
        ("yes", "Yes"),
        ("maybe", "Maybe"),
        ("no", "No"),
        ("strong_no", "Strong No"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_session = models.ForeignKey(
        LiveInterviewSession,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)

    # Scores (same structure as SessionReport)
    overall_score = models.FloatField(default=0)
    technical_score = models.FloatField(default=0)
    communication_score = models.FloatField(default=0)
    behavioral_score = models.FloatField(default=0)
    mindset_score = models.FloatField(default=0)

    # AI-generated insights
    summary = models.TextField(blank=True)
    key_strengths = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)

    # Interviewer-specific content
    hiring_recommendation = models.CharField(
        max_length=20,
        choices=HIRING_RECOMMENDATION_CHOICES,
        blank=True
    )
    interviewer_comments = models.TextField(blank=True)

    # Report files (stored in MinIO)
    report_pdf_url = models.URLField(max_length=500, blank=True)

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]
        unique_together = ["live_session", "report_type"]
        indexes = [
            models.Index(fields=["live_session", "report_type"]),
            models.Index(fields=["generated_at"]),
            models.Index(fields=["overall_score"]),
        ]

    def __str__(self):
        return f"{self.report_type.title()} Report for {self.live_session}"


class AIProvider(models.Model):
    """
    Configuration for AI/LLM providers (supports multiple providers).
    Enables easy switching between OpenAI, Anthropic, local models, etc.
    """
    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic Claude"),
        ("local", "Local Model"),
        ("google", "Google AI"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)

    # Provider configuration
    api_key_encrypted = models.CharField(max_length=500)  # Encrypted using Fernet
    model_name = models.CharField(max_length=100)  # e.g., "gpt-3.5-turbo", "claude-3-sonnet"
    base_url = models.URLField(max_length=500, blank=True)  # For custom/local endpoints

    # Capabilities
    supports_question_generation = models.BooleanField(default=True)
    supports_feedback_analysis = models.BooleanField(default=True)
    supports_transcription = models.BooleanField(default=False)

    # Model settings
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)
    additional_config = models.JSONField(default=dict)  # For provider-specific settings

    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_default"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider_type} - {self.model_name})"

    def save(self, *args, **kwargs):
        """Ensure only one default provider"""
        if self.is_default:
            AIProvider.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class SpeechProvider(models.Model):
    """
    Configuration for speech-to-text and text-to-speech providers.
    """
    PROVIDER_CHOICES = [
        ("openai_whisper", "OpenAI Whisper"),
        ("assemblyai", "AssemblyAI"),
        ("google_cloud", "Google Cloud Speech"),
    ]

    SERVICE_TYPE_CHOICES = [
        ("stt", "Speech-to-Text"),
        ("tts", "Text-to-Speech"),
        ("both", "Both STT and TTS"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    service_type = models.CharField(max_length=10, choices=SERVICE_TYPE_CHOICES)

    # Provider configuration
    api_key_encrypted = models.CharField(max_length=500, blank=True)  # Not needed for local Whisper
    base_url = models.URLField(max_length=500, blank=True)

    # Configuration
    language_support = models.JSONField(default=list)  # ["en", "es", "fr"]
    additional_config = models.JSONField(default=dict)

    # Status
    is_active = models.BooleanField(default=True)
    is_default_stt = models.BooleanField(default=False)
    is_default_tts = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider_type"]),
            models.Index(fields=["service_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_default_stt"]),
            models.Index(fields=["is_default_tts"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.provider_type} - {self.service_type})"

    def save(self, *args, **kwargs):
        """Ensure only one default STT and one default TTS provider"""
        if self.is_default_stt and self.service_type in ["stt", "both"]:
            SpeechProvider.objects.filter(is_default_stt=True).update(is_default_stt=False)
        if self.is_default_tts and self.service_type in ["tts", "both"]:
            SpeechProvider.objects.filter(is_default_tts=True).update(is_default_tts=False)
        super().save(*args, **kwargs)
