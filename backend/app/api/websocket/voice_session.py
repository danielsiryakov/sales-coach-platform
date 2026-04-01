import asyncio
import json
import base64
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session_maker
from app.core.storage import storage_service
from app.models.database import PracticeSession, CallRecording, SessionStatus
from app.api.websocket.grok_client import GrokVoiceClient
from app.services.analysis_service import AnalysisService

router = APIRouter()


class VoiceSessionManager:
    """Manages a single voice practice session."""

    def __init__(self, session_uuid: str, websocket: WebSocket):
        self.session_uuid = session_uuid
        self.websocket = websocket
        self.grok_client: Optional[GrokVoiceClient] = None

        # Audio buffers
        self.user_audio_chunks: list[bytes] = []
        self.ai_audio_chunks: list[bytes] = []

        # Transcript
        self.transcript: list[dict] = []
        self.current_ai_text = ""
        self.current_user_text = ""

        # Timing
        self.started_at: Optional[datetime] = None
        self.session_start_time: Optional[float] = None

        # State
        self.is_active = False

    async def start(self, system_prompt: str, voice: str = "Rex") -> bool:
        """Start the voice session."""
        self.grok_client = GrokVoiceClient(
            on_audio=self._on_ai_audio,
            on_transcript=self._on_transcript,
            on_error=self._on_error,
            on_turn_end=self._on_turn_end,
        )

        success = await self.grok_client.connect(system_prompt, voice)
        if success:
            self.is_active = True
            self.started_at = datetime.utcnow()
            self.session_start_time = asyncio.get_event_loop().time()
            return True
        return False

    def _on_ai_audio(self, audio_bytes: bytes):
        """Handle audio from AI."""
        self.ai_audio_chunks.append(audio_bytes)

        # Forward to browser
        asyncio.create_task(self._send_audio_to_client(audio_bytes))

    async def _send_audio_to_client(self, audio_bytes: bytes):
        """Send audio chunk to browser."""
        try:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            await self.websocket.send_json({
                "type": "audio",
                "audio": audio_b64,
            })
        except Exception:
            pass

    def _on_transcript(self, speaker: str, text: str):
        """Handle transcript updates."""
        timestamp_ms = int((asyncio.get_event_loop().time() - self.session_start_time) * 1000)

        if speaker == "ai":
            self.current_ai_text += text
        else:
            # User transcript comes as complete utterance
            self.transcript.append({
                "speaker": "user",
                "text": text,
                "timestamp_ms": timestamp_ms,
            })

            # Send to client
            asyncio.create_task(self._send_transcript_to_client("user", text, timestamp_ms))

    def _on_turn_end(self):
        """Handle end of AI turn."""
        if self.current_ai_text:
            timestamp_ms = int((asyncio.get_event_loop().time() - self.session_start_time) * 1000)
            self.transcript.append({
                "speaker": "ai",
                "text": self.current_ai_text,
                "timestamp_ms": timestamp_ms,
            })

            # Send to client
            asyncio.create_task(
                self._send_transcript_to_client("ai", self.current_ai_text, timestamp_ms)
            )
            self.current_ai_text = ""

    async def _send_transcript_to_client(self, speaker: str, text: str, timestamp_ms: int):
        """Send transcript update to browser."""
        try:
            await self.websocket.send_json({
                "type": "transcript",
                "speaker": speaker,
                "text": text,
                "timestamp_ms": timestamp_ms,
            })
        except Exception:
            pass

    def _on_error(self, error: str):
        """Handle errors from Grok."""
        asyncio.create_task(self._send_error_to_client(error))

    async def _send_error_to_client(self, error: str):
        """Send error to browser."""
        try:
            await self.websocket.send_json({
                "type": "error",
                "message": error,
            })
        except Exception:
            pass

    async def handle_user_audio(self, audio_bytes: bytes):
        """Handle audio from user."""
        self.user_audio_chunks.append(audio_bytes)

        if self.grok_client and self.grok_client.connected:
            await self.grok_client.send_audio(audio_bytes)

    async def stop(self) -> tuple[bytes, bytes, list[dict], int]:
        """Stop the session and return recorded data."""
        self.is_active = False

        if self.grok_client:
            await self.grok_client.disconnect()

        # Combine audio chunks
        user_audio = b"".join(self.user_audio_chunks)
        ai_audio = b"".join(self.ai_audio_chunks)

        # Calculate duration
        duration_seconds = 0
        if self.session_start_time:
            duration_seconds = int(asyncio.get_event_loop().time() - self.session_start_time)

        return user_audio, ai_audio, self.transcript, duration_seconds


# Active sessions storage
active_sessions: Dict[str, VoiceSessionManager] = {}


@router.websocket("/voice/{session_uuid}")
async def voice_session_websocket(websocket: WebSocket, session_uuid: str):
    """WebSocket endpoint for voice practice sessions."""
    await websocket.accept()

    # Get session from database
    async with async_session_maker() as db:
        result = await db.execute(
            select(PracticeSession).where(PracticeSession.session_uuid == session_uuid)
        )
        session = result.scalar_one_or_none()

        if not session:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close()
            return

        if session.status not in [SessionStatus.PENDING, SessionStatus.ACTIVE]:
            await websocket.send_json({"type": "error", "message": "Session already completed"})
            await websocket.close()
            return

        system_prompt = session.system_prompt
        voice = session.voice_id or "Rex"

        # Update session status
        session.status = SessionStatus.ACTIVE
        session.started_at = datetime.utcnow()
        await db.commit()

    # Create session manager
    manager = VoiceSessionManager(session_uuid, websocket)
    active_sessions[session_uuid] = manager

    try:
        # Start voice session with Grok
        success = await manager.start(system_prompt, voice)
        if not success:
            await websocket.send_json({"type": "error", "message": "Failed to connect to voice service"})
            await websocket.close()
            return

        await websocket.send_json({"type": "connected", "session_uuid": session_uuid})

        # Message loop
        while manager.is_active:
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=60)

                if message["type"] == "websocket.disconnect":
                    break

                if "text" in message:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    if msg_type == "audio":
                        # Decode and process user audio
                        audio_b64 = data.get("audio", "")
                        audio_bytes = base64.b64decode(audio_b64)
                        await manager.handle_user_audio(audio_bytes)

                    elif msg_type == "end":
                        # User ended the call
                        break

                    elif msg_type == "interrupt":
                        # User interrupted AI
                        if manager.grok_client:
                            await manager.grok_client.interrupt()

                elif "bytes" in message:
                    # Raw audio bytes
                    await manager.handle_user_audio(message["bytes"])

            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

    finally:
        # Stop session and save data
        user_audio, ai_audio, transcript, duration = await manager.stop()
        del active_sessions[session_uuid]

        # Save to database
        async with async_session_maker() as db:
            result = await db.execute(
                select(PracticeSession).where(PracticeSession.session_uuid == session_uuid)
            )
            session = result.scalar_one_or_none()

            if session:
                session.status = SessionStatus.COMPLETED
                session.ended_at = datetime.utcnow()
                session.duration_seconds = duration

                # Save audio files
                user_audio_path = None
                ai_audio_path = None
                combined_audio_path = None

                if user_audio:
                    user_audio_path = await storage_service.save_audio(
                        session_uuid, user_audio, "user"
                    )
                if ai_audio:
                    ai_audio_path = await storage_service.save_audio(
                        session_uuid, ai_audio, "ai"
                    )
                if user_audio and ai_audio:
                    # Create simple combined audio (interleaved)
                    combined = _combine_audio(user_audio, ai_audio)
                    combined_audio_path = await storage_service.save_audio(
                        session_uuid, combined, "combined"
                    )

                # Create transcript text
                transcript_text = "\n".join([
                    f"[{entry['speaker'].upper()}]: {entry['text']}"
                    for entry in transcript
                ])

                # Create recording record
                recording = CallRecording(
                    session_id=session.id,
                    user_audio_path=user_audio_path,
                    ai_audio_path=ai_audio_path,
                    combined_audio_path=combined_audio_path,
                    transcript=transcript,
                    transcript_text=transcript_text,
                    sample_rate=24000,
                    audio_format="pcm",
                    file_size_bytes=(len(user_audio) + len(ai_audio)),
                )
                db.add(recording)

                await db.commit()

                # Trigger analysis in background
                session.status = SessionStatus.ANALYZING
                await db.commit()

                asyncio.create_task(_run_analysis(session_uuid))

        try:
            await websocket.send_json({
                "type": "session_ended",
                "duration_seconds": duration,
                "transcript_entries": len(transcript),
            })
        except Exception:
            pass


def _combine_audio(user_audio: bytes, ai_audio: bytes) -> bytes:
    """Simple audio combination - just concatenate for now."""
    # In a real implementation, you'd properly mix the audio streams
    # based on timestamps
    return user_audio + ai_audio


async def _run_analysis(session_uuid: str):
    """Run AI analysis on the completed call."""
    # Small delay to ensure database commits are fully visible
    await asyncio.sleep(1)

    try:
        async with async_session_maker() as db:
            analysis_service = AnalysisService(db)
            await analysis_service.analyze_session(session_uuid)
    except Exception as e:
        print(f"Analysis failed for session {session_uuid}: {e}")
        # Update session status to error
        async with async_session_maker() as db:
            result = await db.execute(
                select(PracticeSession).where(PracticeSession.session_uuid == session_uuid)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = SessionStatus.ERROR
                await db.commit()
