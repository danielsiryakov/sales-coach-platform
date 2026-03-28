'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useAudioCapture } from './useAudioCapture';
import { useAudioPlayback } from './useAudioPlayback';
import type { TranscriptEntry } from '@/types';

type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

interface UseVoiceSessionProps {
  sessionUuid: string;
  onSessionEnd?: (duration: number) => void;
}

export function useVoiceSession({ sessionUuid, onSessionEnd }: UseVoiceSessionProps) {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Audio playback for AI responses
  const { queueAudio, stop: stopPlayback, clearQueue } = useAudioPlayback();

  // Handle incoming audio from server
  const handleServerAudio = useCallback((base64Audio: string) => {
    const binaryString = atob(base64Audio);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    queueAudio(bytes.buffer);
  }, [queueAudio]);

  // Send audio to server
  const sendAudio = useCallback((audioData: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const uint8Array = new Uint8Array(audioData);
      let binary = '';
      for (let i = 0; i < uint8Array.length; i++) {
        binary += String.fromCharCode(uint8Array[i]);
      }
      const base64 = btoa(binary);
      wsRef.current.send(JSON.stringify({
        type: 'audio',
        audio: base64,
      }));
    }
  }, []);

  // Audio capture from microphone
  const { isCapturing, startCapture, stopCapture, error: captureError } = useAudioCapture({
    onAudioData: sendAudio,
  });

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (wsRef.current) return;

    setConnectionState('connecting');
    setError(null);
    setTranscript([]);

    const wsUrl = `ws://127.0.0.1:8000/ws/voice/${sessionUuid}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'connected':
            setConnectionState('connected');
            startTimeRef.current = Date.now();
            // Start duration timer
            durationIntervalRef.current = setInterval(() => {
              if (startTimeRef.current) {
                setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000));
              }
            }, 1000);
            // Start audio capture
            startCapture();
            break;

          case 'audio':
            handleServerAudio(data.audio);
            break;

          case 'transcript':
            setTranscript(prev => [...prev, {
              speaker: data.speaker,
              text: data.text,
              timestamp_ms: data.timestamp_ms,
            }]);
            break;

          case 'error':
            setError(data.message);
            setConnectionState('error');
            break;

          case 'session_ended':
            if (onSessionEnd) {
              onSessionEnd(data.duration_seconds);
            }
            break;

          case 'ping':
            // Respond to keepalive
            ws.send(JSON.stringify({ type: 'pong' }));
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('Connection error');
      setConnectionState('error');
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setConnectionState('disconnected');
      stopCapture();
      stopPlayback();

      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [sessionUuid, startCapture, stopCapture, stopPlayback, handleServerAudio, onSessionEnd]);

  // Disconnect and end session
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'end' }));
      wsRef.current.close();
      wsRef.current = null;
    }

    stopCapture();
    stopPlayback();

    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }

    setConnectionState('disconnected');
  }, [stopCapture, stopPlayback]);

  // Interrupt AI speech
  const interrupt = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
      clearQueue();
    }
  }, [clearQueue]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, []);

  // Handle capture errors
  useEffect(() => {
    if (captureError) {
      setError(captureError);
    }
  }, [captureError]);

  return {
    connectionState,
    isCapturing,
    transcript,
    error,
    duration,
    connect,
    disconnect,
    interrupt,
  };
}
