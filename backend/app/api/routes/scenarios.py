from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.database import (
    ScenarioTemplate, BusinessContext, PersonaTrait,
    Objection, CallType, DifficultyLevel
)

router = APIRouter()


class ScenarioTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    call_type: CallType
    objectives: Optional[List[str]]
    difficulty_level: DifficultyLevel
    estimated_duration_minutes: int

    class Config:
        from_attributes = True


class BusinessContextResponse(BaseModel):
    id: int
    trade_name: str
    trade_code: str
    description: Optional[str]
    typical_operations: Optional[List[str]]
    common_risks: Optional[List[str]]
    required_coverages: Optional[List[str]]

    class Config:
        from_attributes = True


class PersonaTraitResponse(BaseModel):
    id: int
    category: str
    name: str
    description: Optional[str]
    difficulty_modifier: float

    class Config:
        from_attributes = True


class ObjectionResponse(BaseModel):
    id: int
    category: str
    objection_text: str
    difficulty_level: DifficultyLevel

    class Config:
        from_attributes = True


@router.get("/templates", response_model=List[ScenarioTemplateResponse])
async def list_scenario_templates(
    call_type: Optional[CallType] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all available scenario templates."""
    query = select(ScenarioTemplate)

    if call_type:
        query = query.where(ScenarioTemplate.call_type == call_type)

    result = await db.execute(query)
    templates = result.scalars().all()

    return [ScenarioTemplateResponse(
        id=t.id,
        name=t.name,
        description=t.description,
        call_type=t.call_type,
        objectives=t.objectives,
        difficulty_level=t.difficulty_level,
        estimated_duration_minutes=t.estimated_duration_minutes,
    ) for t in templates]


@router.get("/templates/{template_id}", response_model=ScenarioTemplateResponse)
async def get_scenario_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific scenario template."""
    template = await db.get(ScenarioTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Scenario template not found")

    return ScenarioTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        call_type=template.call_type,
        objectives=template.objectives,
        difficulty_level=template.difficulty_level,
        estimated_duration_minutes=template.estimated_duration_minutes,
    )


@router.get("/business-contexts", response_model=List[BusinessContextResponse])
async def list_business_contexts(db: AsyncSession = Depends(get_db)):
    """List all available business contexts (trades)."""
    result = await db.execute(select(BusinessContext))
    contexts = result.scalars().all()

    return [BusinessContextResponse(
        id=c.id,
        trade_name=c.trade_name,
        trade_code=c.trade_code,
        description=c.description,
        typical_operations=c.typical_operations,
        common_risks=c.common_risks,
        required_coverages=c.required_coverages,
    ) for c in contexts]


@router.get("/business-contexts/{context_id}", response_model=BusinessContextResponse)
async def get_business_context(
    context_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific business context."""
    context = await db.get(BusinessContext, context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Business context not found")

    return BusinessContextResponse(
        id=context.id,
        trade_name=context.trade_name,
        trade_code=context.trade_code,
        description=context.description,
        typical_operations=context.typical_operations,
        common_risks=context.common_risks,
        required_coverages=context.required_coverages,
    )


@router.get("/traits", response_model=List[PersonaTraitResponse])
async def list_persona_traits(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all available persona traits."""
    query = select(PersonaTrait)

    if category:
        query = query.where(PersonaTrait.category == category)

    result = await db.execute(query)
    traits = result.scalars().all()

    return [PersonaTraitResponse(
        id=t.id,
        category=t.category,
        name=t.name,
        description=t.description,
        difficulty_modifier=t.difficulty_modifier,
    ) for t in traits]


@router.get("/objections", response_model=List[ObjectionResponse])
async def list_objections(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all available objections."""
    query = select(Objection)

    if category:
        query = query.where(Objection.category == category)

    result = await db.execute(query)
    objections = result.scalars().all()

    return [ObjectionResponse(
        id=o.id,
        category=o.category,
        objection_text=o.objection_text,
        difficulty_level=o.difficulty_level,
    ) for o in objections]
