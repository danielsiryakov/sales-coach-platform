'use client';

import { useCallback, useRef, useState } from 'react';

const SAMPLE_RATE = 24000;

export function useAudioPlayback() {
  const [isPlaying, setIsPlaying] = useState(false);

  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<Float32Array[]>([]);
  const isPlayingRef = useRef(false);
  const nextPlayTimeRef = useRef(0);

  const initAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate: SAMPLE_RATE });
    }
    return audioContextRef.current;
  }, []);

  const queueAudio = useCallback((pcmData: ArrayBuffer) => {
    const audioContext = initAudioContext();

    // Convert PCM16 to Float32
    const int16Array = new Int16Array(pcmData);
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768;
    }

    audioQueueRef.current.push(float32Array);

    if (!isPlayingRef.current) {
      playNextChunk();
    }
  }, [initAudioContext]);

  const playNextChunk = useCallback(() => {
    const audioContext = audioContextRef.current;
    if (!audioContext || audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsPlaying(false);
      return;
    }

    isPlayingRef.current = true;
    setIsPlaying(true);

    const chunk = audioQueueRef.current.shift()!;
    const buffer = audioContext.createBuffer(1, chunk.length, SAMPLE_RATE);
    buffer.getChannelData(0).set(chunk);

    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);

    // Schedule playback
    const currentTime = audioContext.currentTime;
    const startTime = Math.max(currentTime, nextPlayTimeRef.current);
    source.start(startTime);

    // Update next play time
    nextPlayTimeRef.current = startTime + buffer.duration;

    // Schedule next chunk
    source.onended = () => {
      playNextChunk();
    };
  }, []);

  const clearQueue = useCallback(() => {
    audioQueueRef.current = [];
    nextPlayTimeRef.current = 0;
  }, []);

  const stop = useCallback(() => {
    clearQueue();
    isPlayingRef.current = false;
    setIsPlaying(false);

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, [clearQueue]);

  return {
    isPlaying,
    queueAudio,
    clearQueue,
    stop,
  };
}
