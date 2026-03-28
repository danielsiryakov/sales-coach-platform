from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.database import (
    PracticeSession, CallScore, SkillEvaluation,
    ImprovementRecommendation, SessionStatus
)

router = APIRouter()


class SkillScoreResponse(BaseModel):
    skill_name: str
    skill_category: str
    score: float
    weight: float
    trend_vs_previous: Optional[float]
    evidence_quotes: Optional[List[str]]


class ScoreDetailResponse(BaseModel):
    session_uuid: str
    overall_score: float
    sales_skills_score: float
    technical_knowledge_score: float
    performance_level: str
    skill_evaluations: List[SkillScoreResponse]
    top_strengths: Optional[List[dict]]
    improvement_areas: Optional[List[dict]]
    coaching_feedback: Optional[str]
    analyzed_at: datetime


class RecommendationResponse(BaseModel):
    id: int
    skill_name: str
    priority: int
    recommendation: str
    example_phrases: Optional[List[str]]
    practice_tips: Optional[List[str]]
    is_active: bool


class DashboardSummaryResponse(BaseModel):
    total_sessions: int
    total_practice_minutes: int
    current_overall_score: Optional[float]
    current_sales_score: Optional[float]
    current_technical_score: Optional[float]
    score_trend_7_days: Optional[float]
    recent_sessions: List[dict]
    skill_averages: Dict[str, float]
    active_recommendations: List[RecommendationResponse]


class ProgressDataPoint(BaseModel):
    date: datetime
    overall_score: float
    sales_score: float
    technical_score: float


@router.get("/session/{session_uuid}/score", response_model=ScoreDetailResponse)
async def get_session_score(
    session_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed score breakdown for a session."""
    result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.score))
        .where(PracticeSession.session_uuid == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.score:
        raise HTTPException(status_code=404, detail="Session has not been scored yet")

    score = session.score

    # Get skill evaluations
    eval_result = await db.execute(
        select(SkillEvaluation).where(SkillEvaluation.call_score_id == score.id)
    )
    evaluations = eval_result.scalars().all()

    skill_responses = [
        SkillScoreResponse(
            skill_name=e.skill_name,
            skill_category=e.skill_category,
            score=e.score,
            weight=e.weight,
            trend_vs_previous=e.trend_vs_previous,
            evidence_quotes=e.evidence_quotes,
        )
        for e in evaluations
    ]

    return ScoreDetailResponse(
        session_uuid=session_uuid,
        overall_score=score.overall_score,
        sales_skills_score=score.sales_skills_score,
        technical_knowledge_score=score.technical_knowledge_score,
        performance_level=score.performance_level,
        skill_evaluations=skill_responses,
        top_strengths=score.top_strengths,
        improvement_areas=score.improvement_areas,
        coaching_feedback=score.coaching_feedback,
        analyzed_at=score.analysis_completed_at or score.created_at,
    )


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary with overall stats and trends."""
    # Total sessions
    total_result = await db.execute(
        select(func.count(PracticeSession.id))
    )
    total_sessions = total_result.scalar() or 0

    # Total practice minutes
    duration_result = await db.execute(
        select(func.sum(PracticeSession.duration_seconds))
        .where(PracticeSession.duration_seconds.isnot(None))
    )
    total_seconds = duration_result.scalar() or 0
    total_minutes = total_seconds // 60

    # Get most recent scored session
    recent_scored_result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.score))
        .where(PracticeSession.status == SessionStatus.SCORED)
        .order_by(desc(PracticeSession.created_at))
        .limit(1)
    )
    recent_scored = recent_scored_result.scalar_one_or_none()

    current_overall = None
    current_sales = None
    current_technical = None

    if recent_scored and recent_scored.score:
        current_overall = recent_scored.score.overall_score
        current_sales = recent_scored.score.sales_skills_score
        current_technical = recent_scored.score.technical_knowledge_score

    # Score trend (7 days ago vs now)
    week_ago = datetime.utcnow() - timedelta(days=7)
    old_scores_result = await db.execute(
        select(CallScore)
        .join(PracticeSession)
        .where(PracticeSession.created_at < week_ago)
        .order_by(desc(PracticeSession.created_at))
        .limit(5)
    )
    old_scores = old_scores_result.scalars().all()

    score_trend = None
    if old_scores and current_overall:
        old_avg = sum(s.overall_score for s in old_scores) / len(old_scores)
        score_trend = current_overall - old_avg

    # Recent sessions
    recent_result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.score))
        .order_by(desc(PracticeSession.created_at))
        .limit(5)
    )
    recent_sessions = recent_result.scalars().all()

    recent_list = []
    for s in recent_sessions:
        session_data = {
            "session_uuid": s.session_uuid,
            "status": s.status.value,
            "persona_name": s.persona_name,
            "created_at": s.created_at.isoformat(),
            "duration_seconds": s.duration_seconds,
        }
        if s.score:
            session_data["overall_score"] = s.score.overall_score
        recent_list.append(session_data)

    # Skill averages from recent 10 scored sessions
    skill_avg_result = await db.execute(
        select(SkillEvaluation)
        .join(CallScore)
        .join(PracticeSession)
        .where(PracticeSession.status == SessionStatus.SCORED)
        .order_by(desc(PracticeSession.created_at))
        .limit(100)  # Up to 10 sessions * ~10 skills each
    )
    skill_evals = skill_avg_result.scalars().all()

    skill_scores: Dict[str, List[float]] = {}
    for e in skill_evals:
        if e.skill_name not in skill_scores:
            skill_scores[e.skill_name] = []
        skill_scores[e.skill_name].append(e.score)

    skill_averages = {
        name: sum(scores) / len(scores)
        for name, scores in skill_scores.items()
    }

    # Active recommendations
    rec_result = await db.execute(
        select(ImprovementRecommendation)
        .where(ImprovementRecommendation.is_active == True)
        .order_by(ImprovementRecommendation.priority)
        .limit(5)
    )
    recommendations = rec_result.scalars().all()

    rec_responses = [
        RecommendationResponse(
            id=r.id,
            skill_name=r.skill_name,
            priority=r.priority,
            recommendation=r.recommendation,
            example_phrases=r.example_phrases,
            practice_tips=r.practice_tips,
            is_active=r.is_active,
        )
        for r in recommendations
    ]

    return DashboardSummaryResponse(
        total_sessions=total_sessions,
        total_practice_minutes=total_minutes,
        current_overall_score=current_overall,
        current_sales_score=current_sales,
        current_technical_score=current_technical,
        score_trend_7_days=score_trend,
        recent_sessions=recent_list,
        skill_averages=skill_averages,
        active_recommendations=rec_responses,
    )


@router.get("/progress", response_model=List[ProgressDataPoint])
async def get_progress_history(
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get score progress over time."""
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.score))
        .where(PracticeSession.status == SessionStatus.SCORED)
        .where(PracticeSession.created_at >= since)
        .order_by(PracticeSession.created_at)
    )
    sessions = result.scalars().all()

    return [
        ProgressDataPoint(
            date=s.created_at,
            overall_score=s.score.overall_score if s.score else 0,
            sales_score=s.score.sales_skills_score if s.score else 0,
            technical_score=s.score.technical_knowledge_score if s.score else 0,
        )
        for s in sessions if s.score
    ]


@router.post("/recommendations/{rec_id}/dismiss")
async def dismiss_recommendation(
    rec_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Dismiss/deactivate a recommendation."""
    rec = await db.get(ImprovementRecommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.is_active = False
    rec.addressed_at = datetime.utcnow()
    await db.commit()

    return {"message": "Recommendation dismissed"}


@router.post("/session/{session_uuid}/generate-feedback")
async def generate_coaching_feedback(
    session_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate detailed coaching feedback for a session on demand."""
    from app.services.analysis_service import AnalysisService

    # Get session with score
    result = await db.execute(
        select(PracticeSession)
        .options(
            selectinload(PracticeSession.score),
            selectinload(PracticeSession.recording),
            selectinload(PracticeSession.scenario_template),
            selectinload(PracticeSession.business_context),
        )
        .where(PracticeSession.session_uuid == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.recording:
        raise HTTPException(status_code=400, detail="Session has no recording")

    # Generate feedback using analysis service
    analysis_service = AnalysisService(db)

    try:
        coaching_feedback = await analysis_service.generate_coaching_feedback(session)

        # Save to score record if it exists
        if session.score:
            session.score.coaching_feedback = coaching_feedback
            await db.commit()

        return {
            "session_uuid": session_uuid,
            "coaching_feedback": coaching_feedback
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate feedback: {str(e)}")
