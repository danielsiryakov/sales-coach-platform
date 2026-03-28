'use client';

import { useEffect, useRef } from 'react';
import type { TranscriptEntry } from '@/types';
import { cn, formatDuration } from '@/lib/utils';
import { User, Bot } from 'lucide-react';

interface TranscriptViewProps {
  transcript: TranscriptEntry[];
  personaName: string;
}

export function TranscriptView({ transcript, personaName }: TranscriptViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  if (transcript.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <p>Conversation will appear here...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {transcript.map((entry, index) => (
        <div
          key={index}
          className={cn(
            'flex',
            entry.speaker === 'user' ? 'justify-end' : 'justify-start'
          )}
        >
          <div
            className={cn(
              'flex max-w-[80%]',
              entry.speaker === 'user' ? 'flex-row-reverse' : 'flex-row'
            )}
          >
            {/* Avatar */}
            <div
              className={cn(
                'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                entry.speaker === 'user'
                  ? 'bg-primary-600 ml-3'
                  : 'bg-gray-700 mr-3'
              )}
            >
              {entry.speaker === 'user' ? (
                <User className="w-5 h-5 text-white" />
              ) : (
                <Bot className="w-5 h-5 text-gray-300" />
              )}
            </div>

            {/* Message */}
            <div>
              <div
                className={cn(
                  'px-4 py-3 rounded-2xl',
                  entry.speaker === 'user'
                    ? 'bg-primary-600 text-white rounded-br-none'
                    : 'bg-gray-700 text-gray-100 rounded-bl-none'
                )}
              >
                <p className="text-sm">{entry.text}</p>
              </div>
              <div
                className={cn(
                  'mt-1 text-xs text-gray-500',
                  entry.speaker === 'user' ? 'text-right' : 'text-left'
                )}
              >
                <span>
                  {entry.speaker === 'user' ? 'You' : personaName}
                </span>
                <span className="mx-1">-</span>
                <span>{formatDuration(Math.floor(entry.timestamp_ms / 1000))}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
