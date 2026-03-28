import asyncio
import json
import base64
import logging
import websockets
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class GrokVoiceClient:
    """Client for Grok Voice API (wss://api.x.ai/v1/realtime)."""

    def __init__(
        self,
        on_audio: Callable[[bytes], None],
        on_transcript: Callable[[str, str], None],  # (speaker, text)
        on_error: Callable[[str], None],
        on_turn_end: Optional[Callable[[], None]] = None,
    ):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.on_audio = on_audio
        self.on_transcript = on_transcript
        self.on_error = on_error
        self.on_turn_end = on_turn_end
        self._connected = False
        self._receive_task: Optional[asyncio.Task] = None

    async def connect(self, system_prompt: str, voice: str = "Rex") -> bool:
        """Connect to Grok Voice API and configure session."""
        try:
            headers = {
                "Authorization": f"Bearer {settings.xai_api_key}",
            }

            self.ws = await websockets.connect(
                settings.grok_voice_url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )

            # Send session configuration
            session_config = {
                "type": "session.update",
                "session": {
                    "model": settings.grok_voice_model,
                    "voice": voice,
                    "instructions": system_prompt,
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 200,
                        "silence_duration_ms": 500,
                        "create_response": True,
                    },
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    }
                }
            }
            logger.info(f"Sending session config with voice={voice}")

            await self.ws.send(json.dumps(session_config))

            # Wait for session confirmation
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            msg = json.loads(response)

            # Grok may respond with different message types
            msg_type = msg.get("type", "")
            if msg_type in ["session.created", "session.updated", "conversation.created"]:
                self._connected = True
                self._receive_task = asyncio.create_task(self._receive_loop())
                return True
            elif msg_type == "error":
                error_msg = msg.get("error", {}).get("message", str(msg))
                self.on_error(f"Session error: {error_msg}")
                return False
            else:
                # For other messages, assume connection is established
                self._connected = True
                self._receive_task = asyncio.create_task(self._receive_loop())
                return True

        except Exception as e:
            self.on_error(f"Connection failed: {str(e)}")
            return False

    async def _receive_loop(self):
        """Background task to receive messages from Grok."""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            self._connected = False
        except Exception as e:
            self.on_error(f"Receive error: {str(e)}")
            self._connected = False

    async def _handle_message(self, message: str):
        """Handle incoming messages from Grok."""
        try:
            msg = json.loads(message)
            msg_type = msg.get("type", "")
            logger.info(f"Grok message received: {msg_type}")

            if msg_type == "response.audio.delta" or msg_type == "response.output_audio.delta":
                # Audio chunk from AI
                audio_b64 = msg.get("delta", "")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    self.on_audio(audio_bytes)
                    logger.debug(f"Received AI audio: {len(audio_bytes)} bytes")

            elif msg_type == "response.audio_transcript.delta" or msg_type == "response.output_audio_transcript.delta":
                # Partial transcript of AI speech
                text = msg.get("delta", "")
                if text:
                    self.on_transcript("ai", text)
                    logger.debug(f"AI transcript: {text}")

            elif msg_type == "conversation.item.input_audio_transcription.completed":
                # Transcript of user speech
                text = msg.get("transcript", "")
                if text:
                    self.on_transcript("user", text)

            elif msg_type == "response.done":
                # AI finished speaking
                if self.on_turn_end:
                    self.on_turn_end()

            elif msg_type == "error":
                error_msg = msg.get("error", {}).get("message", "Unknown error")
                self.on_error(error_msg)

            elif msg_type == "input_audio_buffer.speech_started":
                # User started speaking - could be used for UI feedback
                logger.info("Speech started detected")

            elif msg_type == "input_audio_buffer.speech_stopped":
                # User stopped speaking - commit buffer and trigger response
                logger.info("Speech stopped detected - triggering response")
                # The server VAD should auto-commit, but as fallback:
                if self.ws:
                    try:
                        await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
                        await self.ws.send(json.dumps({"type": "response.create"}))
                    except Exception as e:
                        logger.error(f"Failed to trigger response: {e}")

            elif msg_type == "response.created":
                logger.info("Response created by Grok")

            elif msg_type == "response.output_item.added":
                logger.info(f"Output item added: {msg}")

            elif msg_type == "ping":
                # Respond to ping
                if self.ws:
                    await self.ws.send(json.dumps({"type": "pong"}))
            else:
                logger.debug(f"Unhandled message type: {msg_type}")

        except json.JSONDecodeError:
            logger.error("Failed to parse JSON message")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            self.on_error(f"Message handling error: {str(e)}")

    async def send_audio(self, audio_bytes: bytes):
        """Send audio chunk to Grok."""
        if not self._connected or not self.ws:
            logger.warning("Cannot send audio - not connected")
            return

        try:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            message = {
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
            }
            await self.ws.send(json.dumps(message))
            logger.debug(f"Sent audio chunk: {len(audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"Send audio error: {e}")
            self.on_error(f"Send error: {str(e)}")

    async def commit_audio(self):
        """Commit the audio buffer and trigger response."""
        if not self._connected or not self.ws:
            return

        try:
            await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await self.ws.send(json.dumps({"type": "response.create"}))
        except Exception as e:
            self.on_error(f"Commit error: {str(e)}")

    async def interrupt(self):
        """Interrupt AI speech."""
        if not self._connected or not self.ws:
            return

        try:
            await self.ws.send(json.dumps({"type": "response.cancel"}))
        except Exception as e:
            pass  # Ignore interrupt errors

    async def disconnect(self):
        """Disconnect from Grok."""
        self._connected = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None

    @property
    def connected(self) -> bool:
        return self._connected
