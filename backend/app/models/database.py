from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class CallType(str, enum.Enum):
    COLD_CALL = "cold_call"
    WARM_LEAD = "warm_lead"
    RENEWAL = "renewal"
    CROSS_SELL = "cross_sell"
    CLAIMS = "claims"
    REVIEW = "review"


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SessionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ANALYZING = "analyzing"
    SCORED = "scored"
    ERROR = "error"


class ScenarioTemplate(Base):
    __tablename__ = "scenario_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    call_type = Column(Enum(CallType), nullable=False)
    base_prompt = Column(Text, nullable=False)
    objectives = Column(JSON)  # List of call objectives
    success_criteria = Column(JSON)  # What makes this call successful
    difficulty_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    estimated_duration_minutes = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BusinessContext(Base):
    __tablename__ = "business_contexts"

    id = Column(Integer, primary_key=True, index=True)
    trade_name = Column(String(255), nullable=False)  # e.g., "General Contractor", "Electrician"
    trade_code = Column(String(50), unique=True)  # e.g., "gc", "electrical", "roofing"
    description = Column(Text)
    typical_operations = Column(JSON)  # List of common operations
    common_risks = Column(JSON)  # Industry-specific risks
    required_coverages = Column(JSON)  # List of typically required coverages
    revenue_range = Column(JSON)  # {"min": 100000, "max": 5000000}
    employee_range = Column(JSON)  # {"min": 1, "max": 50}
    subcontractor_usage = Column(Boolean, default=False)
    equipment_intensive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PersonaTrait(Base):
    __tablename__ = "persona_traits"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)  # e.g., "personality", "buying_behavior", "emotional_state"
    name = Column(String(255), nullable=False)  # e.g., "skeptical", "price-focused"
    description = Column(Text)
    behavioral_cues = Column(JSON)  # How this manifests in conversation
    response_patterns = Column(JSON)  # Typical responses
    difficulty_modifier = Column(Float, default=1.0)  # Multiplier for difficulty
    created_at = Column(DateTime, default=datetime.utcnow)


class Objection(Base):
    __tablename__ = "objections"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)  # e.g., "price", "loyalty", "complacency"
    objection_text = Column(Text, nullable=False)
    variations = Column(JSON)  # Alternative phrasings
    response_framework = Column(JSON)  # Suggested response approach
    difficulty_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    created_at = Column(DateTime, default=datetime.utcnow)


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String(36), unique=True, index=True, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING)

    # Configuration
    scenario_template_id = Column(Integer, ForeignKey("scenario_templates.id"))
    business_context_id = Column(Integer, ForeignKey("business_contexts.id"))
    difficulty_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)

    # Generated persona
    persona_name = Column(String(255))
    persona_company = Column(String(255))
    persona_details = Column(JSON)  # Full generated persona
    assigned_traits = Column(JSON)  # List of trait IDs
    assigned_objections = Column(JSON)  # List of objection IDs
    system_prompt = Column(Text)  # Final prompt sent to Grok
    voice_id = Column(String(50), default="Rex")  # Grok voice selection

    # Timing
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scenario_template = relationship("ScenarioTemplate")
    business_context = relationship("BusinessContext")
    recording = relationship("CallRecording", back_populates="session", uselist=False)
    score = relationship("CallScore", back_populates="session", uselist=False)


class CallRecording(Base):
    __tablename__ = "call_recordings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False)

    # Audio storage
    user_audio_path = Column(String(500))  # Path to user audio
    ai_audio_path = Column(String(500))  # Path to AI audio
    combined_audio_path = Column(String(500))  # Path to combined audio

    # Transcript
    transcript = Column(JSON)  # List of {speaker, text, timestamp_ms}
    transcript_text = Column(Text)  # Plain text version

    # Metadata
    sample_rate = Column(Integer, default=24000)
    audio_format = Column(String(50), default="pcm")
    file_size_bytes = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("PracticeSession", back_populates="recording")


class CallScore(Base):
    __tablename__ = "call_scores"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False)

    # Overall scores
    overall_score = Column(Float, nullable=False)  # 0-100
    sales_skills_score = Column(Float, nullable=False)  # 0-100
    technical_knowledge_score = Column(Float, nullable=False)  # 0-100

    # Performance level
    performance_level = Column(String(50))  # Novice/Developing/Proficient/Expert

    # Analysis metadata
    analysis_model = Column(String(100))  # Model used for analysis
    analysis_completed_at = Column(DateTime)
    analysis_duration_seconds = Column(Float)

    # Raw analysis output
    raw_analysis = Column(JSON)

    # Highlighted moments
    top_strengths = Column(JSON)  # List of {skill, evidence_quote, score}
    improvement_areas = Column(JSON)  # List of {skill, evidence_quote, recommendation}

    # Detailed coaching feedback
    coaching_feedback = Column(Text)  # Detailed improvement advice with specific wordings/prices/products

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("PracticeSession", back_populates="score")
    skill_evaluations = relationship("SkillEvaluation", back_populates="call_score")
    recommendations = relationship("ImprovementRecommendation", back_populates="call_score")


class SkillEvaluation(Base):
    __tablename__ = "skill_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    call_score_id = Column(Integer, ForeignKey("call_scores.id"), nullable=False)

    skill_category = Column(String(50), nullable=False)  # "sales" or "technical"
    skill_name = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    weight = Column(Float, nullable=False)  # Weight in category

    # Evidence
    evidence_quotes = Column(JSON)  # List of supporting quotes from transcript
    evaluation_notes = Column(Text)  # AI explanation of score

    # Trend
    trend_vs_previous = Column(Float)  # Difference from last call

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    call_score = relationship("CallScore", back_populates="skill_evaluations")


class ImprovementRecommendation(Base):
    __tablename__ = "improvement_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    call_score_id = Column(Integer, ForeignKey("call_scores.id"), nullable=False)

    skill_name = Column(String(100), nullable=False)
    priority = Column(Integer, nullable=False)  # 1 = highest priority

    recommendation = Column(Text, nullable=False)
    example_phrases = Column(JSON)  # Suggested phrases to use
    practice_tips = Column(JSON)  # Tips for improvement

    # Status tracking
    is_active = Column(Boolean, default=True)
    addressed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    call_score = relationship("CallScore", back_populates="recommendations")


class ProducerSkillProgress(Base):
    __tablename__ = "producer_skill_progress"

    id = Column(Integer, primary_key=True, index=True)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Aggregated scores
    overall_score_avg = Column(Float)
    sales_skills_avg = Column(Float)
    technical_knowledge_avg = Column(Float)

    # Per-skill averages
    skill_scores = Column(JSON)  # {skill_name: avg_score}

    # Session counts
    total_sessions = Column(Integer, default=0)
    total_duration_minutes = Column(Integer, default=0)

    # Trends
    score_trend = Column(Float)  # Change from previous period

    created_at = Column(DateTime, default=datetime.utcnow)
