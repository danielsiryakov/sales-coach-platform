from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import io

from app.core.database import get_db
from app.core.storage import storage_service
from app.models.database import PracticeSession, CallRecording

router = APIRouter()


class TranscriptEntry(BaseModel):
    speaker: str  # "user" or "ai"
    text: str
    timestamp_ms: int


class RecordingResponse(BaseModel):
    id: int
    session_uuid: str
    has_user_audio: bool
    has_ai_audio: bool
    has_combined_audio: bool
    transcript: Optional[List[TranscriptEntry]]
    transcript_text: Optional[str]
    sample_rate: int
    audio_format: str
    duration_seconds: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{session_uuid}", response_model=RecordingResponse)
async def get_recording(
    session_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    """Get recording metadata and transcript for a session."""
    result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.recording))
        .where(PracticeSession.session_uuid == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.recording:
        raise HTTPException(status_code=404, detail="No recording for this session")

    recording = session.recording

    transcript_entries = None
    if recording.transcript:
        transcript_entries = [
            TranscriptEntry(**entry) for entry in recording.transcript
        ]

    return RecordingResponse(
        id=recording.id,
        session_uuid=session_uuid,
        has_user_audio=bool(recording.user_audio_path),
        has_ai_audio=bool(recording.ai_audio_path),
        has_combined_audio=bool(recording.combined_audio_path),
        transcript=transcript_entries,
        transcript_text=recording.transcript_text,
        sample_rate=recording.sample_rate,
        audio_format=recording.audio_format,
        duration_seconds=session.duration_seconds,
        created_at=recording.created_at,
    )


@router.get("/{session_uuid}/transcript")
async def get_transcript(
    session_uuid: str,
    db: AsyncSession = Depends(get_db)
):
    """Get just the transcript for a session."""
    result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.recording))
        .where(PracticeSession.session_uuid == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.recording:
        raise HTTPException(status_code=404, detail="No recording for this session")

    return {
        "session_uuid": session_uuid,
        "transcript": session.recording.transcript,
        "transcript_text": session.recording.transcript_text,
    }


@router.get("/{session_uuid}/audio/{audio_type}")
async def get_audio(
    session_uuid: str,
    audio_type: str,  # "user", "ai", or "combined"
    db: AsyncSession = Depends(get_db)
):
    """Stream audio file for a session."""
    if audio_type not in ["user", "ai", "combined"]:
        raise HTTPException(status_code=400, detail="Invalid audio type")

    result = await db.execute(
        select(PracticeSession)
        .options(selectinload(PracticeSession.recording))
        .where(PracticeSession.session_uuid == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.recording:
        raise HTTPException(status_code=404, detail="No recording for this session")

    recording = session.recording

    path_map = {
        "user": recording.user_audio_path,
        "ai": recording.ai_audio_path,
        "combined": recording.combined_audio_path,
    }

    audio_path = path_map.get(audio_type)
    if not audio_path:
        raise HTTPException(status_code=404, detail=f"No {audio_type} audio available")

    audio_data = await storage_service.get_audio(audio_path)
    if not audio_data:
        raise HTTPException(status_code=404, detail="Audio file not found")

    return StreamingResponse(
        io.BytesIO(audio_data),
        media_type="audio/pcm",
        headers={
            "Content-Disposition": f"attachment; filename={session_uuid}_{audio_type}.pcm",
            "X-Sample-Rate": str(recording.sample_rate),
        }
    )
