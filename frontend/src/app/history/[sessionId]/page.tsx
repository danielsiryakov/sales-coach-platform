'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import { getSession, getSessionScore, getTranscript, generateCoachingFeedback } from '@/lib/api';
import type { SessionDetail, ScoreDetail, TranscriptEntry } from '@/types';
import { formatDateTime, formatDuration, getScoreColor, getScoreBgColor, cn } from '@/lib/utils';
import {
  ArrowLeft,
  Phone,
  Clock,
  User,
  Target,
  TrendingUp,
  TrendingDown,
  MessageSquare,
  Award,
  AlertTriangle,
  Lightbulb,
  Sparkles,
  Loader2,
} from 'lucide-react';

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [score, setScore] = useState<ScoreDetail | null>(null);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'score' | 'transcript' | 'coaching'>('score');
  const [coachingFeedback, setCoachingFeedback] = useState<string | null>(null);
  const [generatingFeedback, setGeneratingFeedback] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const sessionData = await getSession(sessionId);
        setSession(sessionData);

        // Try to load score if session is scored
        if (sessionData.status === 'scored') {
          try {
            const scoreData = await getSessionScore(sessionId);
            setScore(scoreData);
            // Load existing coaching feedback if available
            if (scoreData.coaching_feedback) {
              setCoachingFeedback(scoreData.coaching_feedback);
            }
          } catch (err) {
            console.log('Score not available yet');
          }
        }

        // Load transcript
        try {
          const transcriptData = await getTranscript(sessionId);
          setTranscript(transcriptData.transcript || []);
        } catch (err) {
          console.log('Transcript not available');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [sessionId]);

  const handleGenerateFeedback = async () => {
    setGeneratingFeedback(true);
    setFeedbackError(null);
    try {
      const result = await generateCoachingFeedback(sessionId);
      setCoachingFeedback(result.coaching_feedback);
    } catch (err) {
      setFeedbackError(err instanceof Error ? err.message : 'Failed to generate feedback');
    } finally {
      setGeneratingFeedback(false);
    }
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
        <Link
          href="/history"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Back to History
        </Link>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/history"
          className="inline-flex items-center text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to History
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {session.persona_name || 'Practice Call'}
            </h1>
            <p className="text-gray-500 mt-1">
              {session.scenario_name} - {session.business_context}
            </p>
            <div className="flex items-center mt-2 text-sm text-gray-400">
              <Clock className="w-4 h-4 mr-1" />
              {formatDuration(session.duration_seconds)}
              <span className="mx-2">-</span>
              {formatDateTime(session.created_at)}
            </div>
          </div>
          {score && (
            <div className={cn(
              'px-6 py-4 rounded-xl text-center',
              getScoreBgColor(score.overall_score)
            )}>
              <div className={cn('text-4xl font-bold', getScoreColor(score.overall_score))}>
                {Math.round(score.overall_score)}
              </div>
              <div className="text-sm text-gray-600">Overall Score</div>
              <div className={cn('text-sm font-medium', getScoreColor(score.overall_score))}>
                {score.performance_level}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      {score && (
        <div className="border-b border-gray-200 mb-6">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('score')}
              className={cn(
                'pb-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'score'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              Score Analysis
            </button>
            <button
              onClick={() => setActiveTab('transcript')}
              className={cn(
                'pb-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'transcript'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              Transcript
            </button>
            <button
              onClick={() => setActiveTab('coaching')}
              className={cn(
                'pb-4 text-sm font-medium border-b-2 transition-colors flex items-center',
                activeTab === 'coaching'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <Sparkles className="w-4 h-4 mr-1" />
              AI Coaching
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      {activeTab === 'score' && score ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Score Details */}
          <div className="lg:col-span-2 space-y-8">
            {/* Score Breakdown */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Score Breakdown
              </h2>
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className={cn('p-4 rounded-lg', getScoreBgColor(score.sales_skills_score))}>
                  <div className={cn('text-2xl font-bold', getScoreColor(score.sales_skills_score))}>
                    {Math.round(score.sales_skills_score)}
                  </div>
                  <div className="text-sm text-gray-600">Sales Skills</div>
                </div>
                <div className={cn('p-4 rounded-lg', getScoreBgColor(score.technical_knowledge_score))}>
                  <div className={cn('text-2xl font-bold', getScoreColor(score.technical_knowledge_score))}>
                    {Math.round(score.technical_knowledge_score)}
                  </div>
                  <div className="text-sm text-gray-600">Technical Knowledge</div>
                </div>
              </div>

              {/* Individual Skills */}
              <div className="space-y-3">
                {score.skill_evaluations.map((skill, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700">
                          {skill.skill_name}
                        </span>
                        <span className={cn('text-sm font-semibold', getScoreColor(skill.score))}>
                          {Math.round(skill.score)}
                        </span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all',
                            skill.score >= 80 ? 'bg-green-500' :
                            skill.score >= 60 ? 'bg-blue-500' :
                            skill.score >= 40 ? 'bg-yellow-500' :
                            'bg-red-500'
                          )}
                          style={{ width: `${skill.score}%` }}
                        />
                      </div>
                    </div>
                    {skill.trend_vs_previous !== null && (
                      <div className={cn(
                        'ml-4 flex items-center text-sm',
                        skill.trend_vs_previous > 0 ? 'text-green-600' : 'text-red-600'
                      )}>
                        {skill.trend_vs_previous > 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Evidence & Quotes */}
            {score.skill_evaluations.some(s => s.evidence_quotes?.length) && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <MessageSquare className="w-5 h-5 mr-2 text-primary-600" />
                  Key Moments
                </h2>
                <div className="space-y-4">
                  {score.skill_evaluations
                    .filter(s => s.evidence_quotes?.length)
                    .slice(0, 5)
                    .map((skill, i) => (
                      <div key={i} className="border-l-4 border-primary-200 pl-4">
                        <p className="text-sm font-medium text-gray-700 mb-1">
                          {skill.skill_name}
                        </p>
                        <p className="text-sm text-gray-600 italic">
                          "{skill.evidence_quotes?.[0]}"
                        </p>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Strengths & Improvements */}
          <div className="space-y-8">
            {/* Top Strengths */}
            {score.top_strengths && score.top_strengths.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Award className="w-5 h-5 mr-2 text-green-600" />
                  Top Strengths
                </h2>
                <div className="space-y-4">
                  {score.top_strengths.map((strength, i) => (
                    <div key={i} className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-green-800">{strength.skill}</span>
                        <span className="text-green-600 font-semibold">{strength.score}</span>
                      </div>
                      <p className="text-sm text-green-700 italic">
                        "{strength.evidence_quote}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Improvement Areas */}
            {score.improvement_areas && score.improvement_areas.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Lightbulb className="w-5 h-5 mr-2 text-yellow-600" />
                  Areas to Improve
                </h2>
                <div className="space-y-4">
                  {score.improvement_areas.map((area, i) => (
                    <div key={i} className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="font-medium text-yellow-800 mb-2">{area.skill}</p>
                      <p className="text-sm text-yellow-700 mb-2">
                        {area.recommendation}
                      </p>
                      {area.evidence_quote && (
                        <p className="text-xs text-yellow-600 italic border-t border-yellow-200 pt-2 mt-2">
                          "{area.evidence_quote}"
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      ) : activeTab === 'coaching' ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <Sparkles className="w-6 h-6 mr-2 text-purple-600" />
              AI Coaching Feedback
            </h2>
            {coachingFeedback && (
              <button
                onClick={handleGenerateFeedback}
                disabled={generatingFeedback}
                className={cn(
                  "inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  generatingFeedback
                    ? "bg-gray-200 text-gray-500 cursor-not-allowed"
                    : "bg-purple-100 text-purple-700 hover:bg-purple-200"
                )}
              >
                {generatingFeedback ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Regenerating...
                  </>
                ) : (
                  'Regenerate'
                )}
              </button>
            )}
          </div>

          {coachingFeedback ? (
            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-6">
              <div className="prose prose-purple max-w-none prose-headings:text-purple-900 prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-3 prose-h3:text-lg prose-h3:mt-4 prose-h3:mb-2 prose-p:text-gray-700 prose-strong:text-purple-800 prose-li:text-gray-700 prose-ul:my-2 prose-ol:my-2 prose-blockquote:border-purple-300 prose-blockquote:bg-white prose-blockquote:rounded prose-blockquote:py-1 prose-blockquote:text-gray-600 prose-blockquote:italic">
                <ReactMarkdown>{coachingFeedback}</ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              {feedbackError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 max-w-md mx-auto">
                  <p className="text-red-600 text-sm">{feedbackError}</p>
                </div>
              )}
              <Sparkles className="w-16 h-16 mx-auto text-purple-300 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Get Personalized Coaching
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Our AI coach will analyze your call and provide specific feedback with exact quotes from the conversation,
                better scripts to use, and detailed product knowledge you could have shared.
              </p>
              <button
                onClick={handleGenerateFeedback}
                disabled={generatingFeedback}
                className={cn(
                  "inline-flex items-center px-8 py-4 rounded-xl font-semibold text-lg transition-all shadow-lg",
                  generatingFeedback
                    ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                    : "bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700"
                )}
              >
                {generatingFeedback ? (
                  <>
                    <Loader2 className="w-6 h-6 mr-3 animate-spin" />
                    Analyzing Your Call...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-6 h-6 mr-3" />
                    Generate Coaching Feedback
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      ) : activeTab === 'transcript' ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Conversation Transcript
          </h2>
          {transcript.length > 0 ? (
            <div className="space-y-4">
              {transcript.map((entry, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex',
                    entry.speaker === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={cn(
                      'max-w-[70%] px-4 py-3 rounded-2xl',
                      entry.speaker === 'user'
                        ? 'bg-primary-600 text-white rounded-br-none'
                        : 'bg-gray-100 text-gray-800 rounded-bl-none'
                    )}
                  >
                    <p className="text-sm">{entry.text}</p>
                    <p className={cn(
                      'text-xs mt-1',
                      entry.speaker === 'user' ? 'text-primary-200' : 'text-gray-400'
                    )}>
                      {formatDuration(Math.floor(entry.timestamp_ms / 1000))}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-400 py-8">No transcript available</p>
          )}
        </div>
      ) : session.status === 'analyzing' ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Analyzing Your Call
          </h2>
          <p className="text-gray-500">
            AI is reviewing your conversation and generating feedback...
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Score Not Available
          </h2>
          <p className="text-gray-500">
            This session has not been scored yet.
          </p>
        </div>
      )}
    </div>
  );
}
