'use client';

import { useCallback, useRef, useState } from 'react';

const SAMPLE_RATE = 24000;

interface UseAudioCaptureProps {
  onAudioData: (data: ArrayBuffer) => void;
}

export function useAudioCapture({ onAudioData }: UseAudioCaptureProps) {
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const startCapture = useCallback(async () => {
    try {
      setError(null);

      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      // Create audio context
      const audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
      audioContextRef.current = audioContext;

      // Load audio worklet
      await audioContext.audioWorklet.addModule('/worklets/audio-capture-processor.js');

      // Create worklet node
      const workletNode = new AudioWorkletNode(audioContext, 'audio-capture-processor');
      workletNodeRef.current = workletNode;

      // Handle audio data from worklet
      workletNode.port.onmessage = (event) => {
        if (event.data.type === 'audio') {
          onAudioData(event.data.buffer);
        }
      };

      // Connect microphone to worklet
      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;
      source.connect(workletNode);

      setIsCapturing(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start audio capture';
      setError(message);
      console.error('Audio capture error:', err);
    }
  }, [onAudioData]);

  const stopCapture = useCallback(() => {
    // Disconnect and clean up
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setIsCapturing(false);
  }, []);

  return {
    isCapturing,
    error,
    startCapture,
    stopCapture,
  };
}
