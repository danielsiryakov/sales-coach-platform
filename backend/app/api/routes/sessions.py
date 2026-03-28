from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.database import (
    PracticeSession, SessionStatus, DifficultyLevel,
    ScenarioTemplate, BusinessContext, CallScore
)
from app.services.persona_generator import PersonaGenerator

router = APIRouter()


class SessionCreateRequest(BaseModel):
    scenario_template_id: int
    business_context_id: int
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    voice_id: str = "Rex"


class SessionResponse(BaseModel):
    id: int
    session_uuid: str
    status: SessionStatus
    persona_name: Optional[str]
    persona_company: Optional[str]
    scenario_name: Optional[str]
    business_context: Optional[str]
    difficulty_level: DifficultyLevel
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    persona_details: Optional[dict]
    system_prompt: Optional[str]
    voice_id: str
    overall_score: Optional[float] = None
    sales_skills_score: Optional[float] = None
    technical_knowledge_score: Optional[float] = None


@router.post("/", response_model=SessionDetailResponse)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new practice session with generated persona."""
    # Verify scenario and business context exist
    scenario = await db.get(ScenarioTemplate, request.scenario_template_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario template not found")

    business_context = await db.get(BusinessContext, request.business_context_id)
    if not business_context:
        raise HTTPException(status_code=404, detail="Business context not found")

    # Generate persona
    persona_generator = PersonaGenerator(db)
    persona = await persona_generator.generate(
        scenario_template=scenario,
        business_context=business_context,
        difficulty_level=request.difficulty_level
    )

    # Create session
    session = PracticeSession(
        session_uuid=str(uuid.uuid4()),
        status=SessionStatus.PENDING,
        scenario_template_id=request.scenario_template_id,
        business_context_id=request.business_context_id,
        difficulty_level=request.difficulty_level,
        persona_name=persona["name"],
        persona_company=persona["company"],
        persona_details=persona,
        assigned_traits=persona.get("trait_ids", []),
        assigned_objections=persona.get("objection_ids", []),
        system_prompt=persona["system_prompt"],
        voice_id=request.voice_id,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionDetailResponse(
        id=session.id,
        session_uuid=session.session_uuid,
        status=session.status,
        persona_name=session.persona_name,
        persona_company=session.persona_company,
        scenario_name=scenario.name,
        business_context=business_context.trade_name,
        difficulty_level=session.difficulty_level,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        created_at=session.created_at,
        persona_details=session.persona_details,
        system_prompt=session.system_prompt,
        voice_id=session.voice_id,
    )


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    status: Optional[SessionStatus] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List practice sessions with optional filtering."""
    query = select(PracticeSession).order_by(desc(PracticeSession.created_at))

    if status:
        query = query.where(PracticeSession.status == status)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()

    responses = []
    for session in sessions:
        scenario_name = None
        business_context_name = None

        if session.scenario_template_id:
            scenario = await db.get(ScenarioTemplate, session.scenario_template_id)
            scenario_name = scenario.name if scenario else None

        if session.business_context_id:
            bc = await db.get(BusinessContext, session.business_context_id)
            business_context_name = bc.trade_name if bc else None

        responses.append(SessionResponse(
            id=session.id,
            session_uuid=session.session_uuid,
            status=session.status,
            persona_name=session.persona_name,
            persona_company=session.persona_company,
            scenario_name=scenario_name,
            business_context=business_context_name,
            difficulty_level=session.difficulty_level,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_seconds=session.duration_seconds,
            created_at=session.created_at,
        ))

    return responses


@router.get("/{session_uuid}", response_model=SessionDetailResponse)
async def get_session(
    session_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific session."""
    # Use selectinload to eagerly load the score relationship
    result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.score))
        .where(PracticeSession.session_uuid == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    scenario_name = None
    business_context_name = None
    overall_score = None
    sales_score = None
    technical_score = None

    if session.scenario_template_id:
        scenario = await db.get(ScenarioTemplate, session.scenario_template_id)
        scenario_name = scenario.name if scenario else None

    if session.business_context_id:
        bc = await db.get(BusinessContext, session.business_context_id)
        business_context_name = bc.trade_name if bc else None

    # score is now eagerly loaded, safe to access
    if session.score:
        overall_score = session.score.overall_score
        sales_score = session.score.sales_skills_score
        technical_score = session.score.technical_knowledge_score

    return SessionDetailResponse(
        id=session.id,
        session_uuid=session.session_uuid,
        status=session.status,
        persona_name=session.persona_name,
        persona_company=session.persona_company,
        scenario_name=scenario_name,
        business_context=business_context_name,
        difficulty_level=session.difficulty_level,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        created_at=session.created_at,
        persona_details=session.persona_details,
        system_prompt=session.system_prompt,
        voice_id=session.voice_id,
        overall_score=overall_score,
        sales_skills_score=sales_score,
        technical_knowledge_score=technical_score,
    )


@router.delete("/{session_uuid}")
async def delete_session(
    session_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a practice session."""
    result = await db.execute(
        select(PracticeSession).where(PracticeSession.session_uuid == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    return {"message": "Session deleted"}
