'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { getSession } from '@/lib/api';
import type { SessionDetail } from '@/types';
import { useVoiceSession } from '@/hooks/useVoiceSession';
import { VoiceControls } from '@/components/voice/VoiceControls';
import { TranscriptView } from '@/components/voice/TranscriptView';
import { CallInfo } from '@/components/voice/CallInfo';
import { cn, formatDuration } from '@/lib/utils';
import { Phone, PhoneOff, User, Mic, MicOff } from 'lucide-react';

export default function ActiveCallPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [callEnded, setCallEnded] = useState(false);

  const {
    connectionState,
    isCapturing,
    transcript,
    error: voiceError,
    duration,
    connect,
    disconnect,
  } = useVoiceSession({
    sessionUuid: sessionId,
    onSessionEnd: (endDuration) => {
      setCallEnded(true);
      // Redirect to results after a short delay
      setTimeout(() => {
        router.push(`/history/${sessionId}`);
      }, 2000);
    },
  });

  useEffect(() => {
    async function loadSession() {
      try {
        const data = await getSession(sessionId);
        setSession(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session');
      } finally {
        setLoading(false);
      }
    }

    loadSession();
  }, [sessionId]);

  const handleStartCall = () => {
    connect();
  };

  const handleEndCall = () => {
    disconnect();
    setCallEnded(true);
    setTimeout(() => {
      router.push(`/history/${sessionId}`);
    }, 2000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-red-600 mb-4">{error || 'Session not found'}</p>
        <button
          onClick={() => router.push('/practice')}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Go Back
        </button>
      </div>
    );
  }

  const isConnected = connectionState === 'connected';
  const isConnecting = connectionState === 'connecting';

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={cn(
              'w-3 h-3 rounded-full mr-3',
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
            )} />
            <div>
              <h1 className="text-lg font-semibold text-white">
                {isConnected ? 'Call in Progress' : callEnded ? 'Call Ended' : 'Ready to Call'}
              </h1>
              <p className="text-sm text-gray-400">
                {session.persona_name} - {session.persona_company}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-2xl font-mono text-white">
              {formatDuration(duration)}
            </div>
            {isCapturing && (
              <div className="flex items-center text-green-400">
                <Mic className="w-5 h-5 mr-1 animate-pulse" />
                <span className="text-sm">Live</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Transcript */}
        <div className="flex-1 overflow-auto p-6">
          {connectionState === 'disconnected' && !callEnded && transcript.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-24 h-24 bg-gray-800 rounded-full flex items-center justify-center mb-6">
                <User className="w-12 h-12 text-gray-500" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">
                {session.persona_name}
              </h2>
              <p className="text-gray-400 mb-1">{session.persona_company}</p>
              <p className="text-gray-500 text-sm mb-8">
                {session.scenario_name} - {session.business_context}
              </p>
              <button
                onClick={handleStartCall}
                disabled={isConnecting}
                className={cn(
                  'flex items-center px-8 py-4 rounded-full font-semibold text-lg transition-all',
                  isConnecting
                    ? 'bg-gray-700 text-gray-400'
                    : 'bg-green-600 text-white hover:bg-green-500'
                )}
              >
                {isConnecting ? (
                  <>
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Phone className="w-6 h-6 mr-3" />
                    Start Call
                  </>
                )}
              </button>
            </div>
          ) : callEnded ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-24 h-24 bg-primary-900 rounded-full flex items-center justify-center mb-6">
                <PhoneOff className="w-12 h-12 text-primary-400" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">
                Call Ended
              </h2>
              <p className="text-gray-400 mb-4">
                Duration: {formatDuration(duration)}
              </p>
              <p className="text-gray-500">
                Analyzing your call...
              </p>
              <div className="mt-4 animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
            </div>
          ) : (
            <TranscriptView
              transcript={transcript}
              personaName={session.persona_name || 'Prospect'}
            />
          )}
        </div>

        {/* Call Info Sidebar */}
        {isConnected && (
          <div className="w-80 bg-gray-800 border-l border-gray-700 p-6 overflow-auto">
            <CallInfo session={session} />
          </div>
        )}
      </div>

      {/* Voice Error */}
      {voiceError && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg">
          {voiceError}
        </div>
      )}

      {/* Controls */}
      {isConnected && (
        <VoiceControls
          isCapturing={isCapturing}
          onEndCall={handleEndCall}
        />
      )}
    </div>
  );
}
