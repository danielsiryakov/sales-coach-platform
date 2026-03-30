'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listSessions, deleteSession } from '@/lib/api';
import type { Session } from '@/types';
import { formatDateTime, formatDuration, getScoreColor, cn } from '@/lib/utils';
import { Phone, Clock, ChevronRight, User, Filter, Trash2, X } from 'lucide-react';

export default function HistoryPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function loadSessions() {
    try {
      setLoading(true);
      const data = await listSessions(statusFilter || undefined);
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSessions();
  }, [statusFilter]);

  const handleDelete = async (sessionUuid: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDeleteConfirm(sessionUuid);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;

    setDeleting(true);
    try {
      await deleteSession(deleteConfirm);
      setSessions(sessions.filter(s => s.session_uuid !== deleteConfirm));
      setDeleteConfirm(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete session');
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
          <p className="text-gray-500 mt-1">
            Review your past practice sessions
          </p>
        </div>
        <Link
          href="/practice"
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Phone className="w-5 h-5 mr-2" />
          New Practice Call
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-3">
        <Filter className="w-5 h-5 text-gray-400" />
        <button
          onClick={() => setStatusFilter(null)}
          className={cn(
            'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
            !statusFilter
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          All
        </button>
        <button
          onClick={() => setStatusFilter('scored')}
          className={cn(
            'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
            statusFilter === 'scored'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          Scored
        </button>
        <button
          onClick={() => setStatusFilter('analyzing')}
          className={cn(
            'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
            statusFilter === 'analyzing'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          )}
        >
          Analyzing
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Delete Session?</h3>
              <button
                onClick={() => setDeleteConfirm(null)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-gray-600 mb-6">
              This will permanently delete this practice session, including the recording, transcript, scores, and all analysis data. This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Phone className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            No sessions found
          </h2>
          <p className="text-gray-500 mb-6">
            {statusFilter
              ? `No sessions with status "${statusFilter}"`
              : 'Start your first practice call to see your history here'
            }
          </p>
          <Link
            href="/practice"
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Phone className="w-5 h-5 mr-2" />
            Start Practice Call
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="divide-y divide-gray-200">
            {sessions.map((session) => (
              <Link
                key={session.session_uuid}
                href={`/history/${session.session_uuid}`}
                className="flex items-center justify-between p-6 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="ml-4">
                    <p className="font-semibold text-gray-900">
                      {session.persona_name || 'Practice Call'}
                    </p>
                    <p className="text-sm text-gray-500">
                      {session.scenario_name} - {session.business_context}
                    </p>
                    <div className="flex items-center mt-1 text-xs text-gray-400">
                      <Clock className="w-3 h-3 mr-1" />
                      {formatDuration(session.duration_seconds)}
                      <span className="mx-2">-</span>
                      {formatDateTime(session.created_at)}
                      <span className="mx-2">-</span>
                      <span className={cn(
                        'capitalize',
                        session.status === 'scored' ? 'text-green-600' :
                        session.status === 'analyzing' ? 'text-yellow-600' :
                        session.status === 'error' ? 'text-red-600' :
                        'text-gray-400'
                      )}>
                        {session.status}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center">
                  {session.overall_score !== null && session.overall_score !== undefined ? (
                    <div className="text-right mr-4">
                      <span className={cn(
                        'text-2xl font-bold',
                        getScoreColor(session.overall_score)
                      )}>
                        {Math.round(session.overall_score)}
                      </span>
                      <p className="text-xs text-gray-400">Overall</p>
                    </div>
                  ) : session.status === 'analyzing' ? (
                    <div className="mr-4 flex items-center text-yellow-600">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600 mr-2" />
                      <span className="text-sm">Analyzing...</span>
                    </div>
                  ) : null}
                  <button
                    onClick={(e) => handleDelete(session.session_uuid, e)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors mr-2"
                    title="Delete session"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
