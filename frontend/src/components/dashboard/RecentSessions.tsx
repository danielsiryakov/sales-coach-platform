'use client';

import Link from 'next/link';
import { formatDateTime, formatDuration, getScoreColor, cn } from '@/lib/utils';
import { ChevronRight, Clock, User } from 'lucide-react';

interface Session {
  session_uuid: string;
  status: string;
  persona_name: string | null;
  created_at: string;
  duration_seconds: number | null;
  overall_score?: number;
}

interface RecentSessionsProps {
  sessions: Session[];
}

export function RecentSessions({ sessions }: RecentSessionsProps) {
  if (!sessions || sessions.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8">
        No sessions yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sessions.map((session) => (
        <Link
          key={session.session_uuid}
          href={`/history/${session.session_uuid}`}
          className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-primary-600" />
            </div>
            <div className="ml-3">
              <p className="font-medium text-gray-900">
                {session.persona_name || 'Practice Call'}
              </p>
              <div className="flex items-center text-sm text-gray-500">
                <Clock className="w-3 h-3 mr-1" />
                {formatDuration(session.duration_seconds)}
                <span className="mx-2">-</span>
                {formatDateTime(session.created_at)}
              </div>
            </div>
          </div>
          <div className="flex items-center">
            {session.overall_score !== undefined ? (
              <span className={cn(
                'font-semibold text-lg mr-3',
                getScoreColor(session.overall_score)
              )}>
                {Math.round(session.overall_score)}
              </span>
            ) : (
              <span className="text-sm text-gray-400 mr-3">
                {session.status === 'analyzing' ? 'Analyzing...' : 'No score'}
              </span>
            )}
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </div>
        </Link>
      ))}
    </div>
  );
}
