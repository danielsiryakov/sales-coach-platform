import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import openai

from app.core.config import settings
from app.models.database import (
    PracticeSession, CallRecording, CallScore,
    SkillEvaluation, ImprovementRecommendation, SessionStatus,
    ScenarioTemplate, BusinessContext
)

logger = logging.getLogger(__name__)


# Scoring rubric
SALES_SKILLS = {
    "discovery_needs_assessment": {
        "name": "Discovery/Needs Assessment",
        "weight": 0.20,
        "description": "Asks open-ended questions, identifies pain points, uncovers business needs"
    },
    "objection_handling": {
        "name": "Objection Handling",
        "weight": 0.20,
        "description": "Acknowledges concerns, clarifies objections, provides evidence, resolves effectively"
    },
    "building_rapport": {
        "name": "Building Rapport",
        "weight": 0.15,
        "description": "Natural conversation flow, genuine interest, finds common ground"
    },
    "closing_techniques": {
        "name": "Closing Techniques",
        "weight": 0.15,
        "description": "Trial closes, asks for commitment, establishes clear next steps"
    },
    "active_listening": {
        "name": "Active Listening",
        "weight": 0.15,
        "description": "Summarizes prospect statements, asks relevant follow-ups, acknowledges points"
    },
    "value_proposition": {
        "name": "Value Proposition",
        "weight": 0.15,
        "description": "Tailors benefits to prospect needs, differentiates from competitors"
    },
}

TECHNICAL_SKILLS = {
    "insurance_terminology": {
        "name": "Insurance Terminology",
        "weight": 0.15,
        "description": "Uses correct terminology, explains terms clearly to prospect"
    },
    "product_knowledge": {
        "name": "Product Knowledge",
        "weight": 0.25,
        "description": "Demonstrates knowledge of GL, WC, Auto, Umbrella, Builder's Risk"
    },
    "construction_industry_risks": {
        "name": "Construction Industry Risks",
        "weight": 0.25,
        "description": "Understands trade-specific hazards, common claims, industry challenges"
    },
    "quoting_coverage": {
        "name": "Quoting/Coverage Discussions",
        "weight": 0.20,
        "description": "Recommends appropriate limits, identifies coverage gaps"
    },
    "regulatory_compliance": {
        "name": "Regulatory Compliance",
        "weight": 0.15,
        "description": "Knows required coverages, state requirements, certificate needs"
    },
}


ANALYSIS_PROMPT = """You are an expert sales coach evaluating a practice call between an insurance producer and a simulated contractor prospect.

## Scoring Rubric

### Sales Skills (60% of overall score)
{sales_skills_rubric}

### Technical Knowledge (40% of overall score)
{technical_skills_rubric}

## Performance Levels
- 0-39: Novice - Significant improvement needed
- 40-59: Developing - Shows potential but needs work
- 60-79: Proficient - Meets expectations with room for growth
- 80-100: Expert - Excellent performance

## Call Context
- Scenario: {scenario_name}
- Prospect Trade: {trade_name}
- Prospect Name: {persona_name}
- Difficulty Level: {difficulty_level}

## Transcript
{transcript}

## Your Task
Analyze this call and provide detailed scoring. For each skill:
1. Assign a score from 0-100
2. Provide 1-2 specific quotes from the transcript as evidence
3. Give a brief explanation of why this score was given

Then identify:
- Top 3 strengths (with evidence)
- Top 3 areas for improvement (with specific recommendations)
- Example phrases the producer could use in future calls

Respond with valid JSON matching this exact schema:
{{
    "overall_score": <number 0-100>,
    "sales_skills_score": <number 0-100>,
    "technical_knowledge_score": <number 0-100>,
    "performance_level": "<Novice|Developing|Proficient|Expert>",
    "skill_evaluations": [
        {{
            "skill_key": "<skill key from rubric>",
            "skill_name": "<skill name>",
            "skill_category": "<sales|technical>",
            "score": <number 0-100>,
            "evidence_quotes": ["<quote from transcript>"],
            "evaluation_notes": "<explanation>"
        }}
    ],
    "top_strengths": [
        {{
            "skill": "<skill name>",
            "evidence_quote": "<quote>",
            "score": <number>
        }}
    ],
    "improvement_areas": [
        {{
            "skill": "<skill name>",
            "evidence_quote": "<quote or description of gap>",
            "recommendation": "<specific actionable recommendation>",
            "example_phrases": ["<suggested phrase>"]
        }}
    ]
}}"""


COACHING_PROMPT = """You are a seasoned commercial insurance producer with 25+ years of experience selling to contractors and construction businesses. You've closed thousands of deals and trained dozens of new producers.

You're doing a post-call tape review with a newer producer who just finished this call. Your job is to break down exactly what happened, what they did well, and—most importantly—what they should have done differently. Be direct, specific, and practical. No fluff.

Think of this like sitting down after a call and saying "Okay, let's rewind the tape. Here's what I noticed..."

## Call Context
- Call Type: {scenario_name}
- Prospect Trade: {trade_name}
- Prospect Name: {persona_name}
- Difficulty Level: {difficulty_level}

## The Call Transcript
{transcript}

---

## Your Tape Review

Write your analysis in a conversational but direct coaching style. Use "you" when talking to the producer and "I" when sharing what you would have done. Be specific—quote the transcript and give exact alternative language.

### 1. The Gut Check
Start with your honest first impression. Was this a good call? Did they control the conversation or get pushed around? One paragraph, straight talk.

### 2. Moments I Would Have Handled Differently
Go through the call chronologically. For each key moment:
- Quote what was said (both sides)
- Explain what you would have done instead and WHY
- Give the exact words you would have used

Example format:
> **At 0:45** - When they said "I just renewed last month"
> You said: "[their response]"
>
> Here's the thing—that's not an objection, that's an opening. I would have said:
> *"Perfect timing actually. No pressure to switch anything now, but that gives us a few months to do a proper review. Most guys who just renewed find out they've been overpaying or have gaps they didn't know about. Let me ask you this—when's the last time someone actually walked through your policy exclusions with you?"*
>
> See the difference? You're not fighting the objection, you're reframing it.

### 3. Objection Handling Breakdown
For each objection the prospect raised, provide:
- The objection (quote it)
- What's really going on in their head (the subtext)
- The response framework that works for this objection
- Word-for-word script to use next time

### 4. What {trade_name} Contractors Actually Care About
Based on this call, share insider knowledge:
- What keeps {trade_name} owners up at night (insurance-wise)
- Trigger phrases you heard that should have led somewhere
- If they mentioned X, you should always ask about Y
- Specific coverage gaps common to this trade
- Premium ranges and what drives them for this business type

### 5. Discovery Gold You Left on the Table
Questions you should have asked based on what they told you. Format:
- When they said "[quote]" → You should have asked: "[specific question]"
- Explain what that question would have uncovered

### 6. The Close
- Did they set a clear next step? Grade it.
- How should they have closed this specific call?
- Give 2-3 closing lines that would have worked here

### 7. Your Homework
End with 2-3 specific things to practice before the next call. Make them actionable and tied to what happened in this call.

---

Remember: Be the mentor who tells it straight. Quote the transcript. Give exact scripts. Share the "insider" knowledge that only comes from years of experience. The goal is for this producer to read your review and think "Okay, I know exactly what to do differently next time."
"""


class AnalysisService:
    """AI-powered call analysis and scoring."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def analyze_session(self, session_uuid: str) -> Optional[CallScore]:
        """Analyze a completed practice session."""
        logger.info(f"Starting analysis for session {session_uuid}")
        start_time = datetime.utcnow()

        # Get session with all related data eagerly loaded
        result = await self.db.execute(
            select(PracticeSession)
            .options(
                selectinload(PracticeSession.recording),
                selectinload(PracticeSession.scenario_template),
                selectinload(PracticeSession.business_context),
            )
            .where(PracticeSession.session_uuid == session_uuid)
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.error(f"Session {session_uuid} not found")
            return None

        if not session.recording:
            logger.error(f"Session {session_uuid} has no recording")
            return None

        logger.info(f"Found session with recording, transcript length: {len(session.recording.transcript_text or '')}")

        # Build analysis prompt
        prompt = self._build_analysis_prompt(session)

        # Check if OpenAI API key is configured
        if not settings.openai_api_key:
            logger.error("OpenAI API key not configured - cannot analyze session")
            session.status = SessionStatus.ERROR
            await self.db.commit()
            return None

        # Call GPT-4 for analysis
        try:
            logger.info(f"Calling OpenAI API for analysis with model {settings.analysis_model}")
            response = await self.client.chat.completions.create(
                model=settings.analysis_model,
                messages=[
                    {"role": "system", "content": "You are an expert insurance sales coach. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"Analysis complete: overall_score={analysis.get('overall_score')}")

        except Exception as e:
            logger.error(f"Analysis API error: {e}")
            session.status = SessionStatus.ERROR
            await self.db.commit()
            return None

        # Get detailed coaching feedback
        coaching_feedback = ""
        try:
            logger.info("Generating coaching feedback...")
            coaching_prompt = self._build_coaching_prompt(session)
            coaching_response = await self.client.chat.completions.create(
                model=settings.analysis_model,
                messages=[
                    {"role": "system", "content": "You are an expert commercial insurance sales coach with 20+ years of experience training producers. Provide specific, actionable coaching advice."},
                    {"role": "user", "content": coaching_prompt}
                ],
                temperature=0.5,
            )
            coaching_feedback = coaching_response.choices[0].message.content
            logger.info(f"Coaching feedback generated: {len(coaching_feedback)} chars")
        except Exception as e:
            logger.error(f"Coaching feedback error: {e}")
            # Continue without coaching feedback - not critical

        # Calculate duration
        analysis_duration = (datetime.utcnow() - start_time).total_seconds()

        # Create CallScore record
        call_score = CallScore(
            session_id=session.id,
            overall_score=analysis["overall_score"],
            sales_skills_score=analysis["sales_skills_score"],
            technical_knowledge_score=analysis["technical_knowledge_score"],
            performance_level=analysis["performance_level"],
            analysis_model=settings.analysis_model,
            analysis_completed_at=datetime.utcnow(),
            analysis_duration_seconds=analysis_duration,
            raw_analysis=analysis,
            top_strengths=analysis.get("top_strengths", []),
            improvement_areas=analysis.get("improvement_areas", []),
            coaching_feedback=coaching_feedback,
        )
        self.db.add(call_score)
        await self.db.flush()

        # Create SkillEvaluation records
        for eval_data in analysis.get("skill_evaluations", []):
            skill_key = eval_data.get("skill_key", "")
            weight = 0

            # Get weight from rubric
            if skill_key in SALES_SKILLS:
                weight = SALES_SKILLS[skill_key]["weight"]
            elif skill_key in TECHNICAL_SKILLS:
                weight = TECHNICAL_SKILLS[skill_key]["weight"]

            skill_eval = SkillEvaluation(
                call_score_id=call_score.id,
                skill_category=eval_data.get("skill_category", "sales"),
                skill_name=eval_data.get("skill_name", skill_key),
                score=eval_data.get("score", 0),
                weight=weight,
                evidence_quotes=eval_data.get("evidence_quotes", []),
                evaluation_notes=eval_data.get("evaluation_notes", ""),
            )
            self.db.add(skill_eval)

        # Create ImprovementRecommendation records
        for priority, area in enumerate(analysis.get("improvement_areas", [])[:3], 1):
            rec = ImprovementRecommendation(
                call_score_id=call_score.id,
                skill_name=area.get("skill", ""),
                priority=priority,
                recommendation=area.get("recommendation", ""),
                example_phrases=area.get("example_phrases", []),
                practice_tips=[],
                is_active=True,
            )
            self.db.add(rec)

        # Update session status
        session.status = SessionStatus.SCORED
        await self.db.commit()

        return call_score

    def _build_analysis_prompt(self, session: PracticeSession) -> str:
        """Build the analysis prompt with context and transcript."""

        # Build rubric descriptions
        sales_rubric = "\n".join([
            f"- {v['name']} ({v['weight']*100:.0f}%): {v['description']}"
            for v in SALES_SKILLS.values()
        ])
        technical_rubric = "\n".join([
            f"- {v['name']} ({v['weight']*100:.0f}%): {v['description']}"
            for v in TECHNICAL_SKILLS.values()
        ])

        # Format transcript
        transcript = session.recording.transcript_text or ""
        if not transcript and session.recording.transcript:
            transcript = "\n".join([
                f"[{entry['speaker'].upper()}]: {entry['text']}"
                for entry in session.recording.transcript
            ])

        # Get context
        scenario_name = "Practice Call"
        trade_name = "Contractor"
        persona_name = session.persona_name or "Prospect"
        difficulty = session.difficulty_level.value if session.difficulty_level else "intermediate"

        if session.scenario_template:
            scenario_name = session.scenario_template.name
        if session.business_context:
            trade_name = session.business_context.trade_name

        return ANALYSIS_PROMPT.format(
            sales_skills_rubric=sales_rubric,
            technical_skills_rubric=technical_rubric,
            scenario_name=scenario_name,
            trade_name=trade_name,
            persona_name=persona_name,
            difficulty_level=difficulty,
            transcript=transcript,
        )

    def _build_coaching_prompt(self, session: PracticeSession) -> str:
        """Build the coaching feedback prompt with context and transcript."""

        # Format transcript
        transcript = session.recording.transcript_text or ""
        if not transcript and session.recording.transcript:
            transcript = "\n".join([
                f"[{entry['speaker'].upper()}]: {entry['text']}"
                for entry in session.recording.transcript
            ])

        # Get context
        scenario_name = "Practice Call"
        trade_name = "Contractor"
        persona_name = session.persona_name or "Prospect"
        difficulty = session.difficulty_level.value if session.difficulty_level else "intermediate"

        if session.scenario_template:
            scenario_name = session.scenario_template.name
        if session.business_context:
            trade_name = session.business_context.trade_name

        return COACHING_PROMPT.format(
            scenario_name=scenario_name,
            trade_name=trade_name,
            persona_name=persona_name,
            difficulty_level=difficulty,
            transcript=transcript,
        )

    async def generate_coaching_feedback(self, session: PracticeSession) -> str:
        """Generate coaching feedback on demand for an existing session."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        if not session.recording:
            raise ValueError("Session has no recording")

        coaching_prompt = self._build_coaching_prompt(session)

        logger.info(f"Generating on-demand coaching feedback for session {session.session_uuid}")

        response = await self.client.chat.completions.create(
            model=settings.analysis_model,
            messages=[
                {"role": "system", "content": "You are an expert commercial insurance sales coach with 20+ years of experience training producers. Provide specific, actionable coaching advice."},
                {"role": "user", "content": coaching_prompt}
            ],
            temperature=0.5,
        )

        coaching_feedback = response.choices[0].message.content
        logger.info(f"Coaching feedback generated: {len(coaching_feedback)} chars")

        return coaching_feedback
