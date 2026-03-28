'use client';

import { useEffect, useState } from 'react';
import { getDashboard, getProgress } from '@/lib/api';
import type { DashboardSummary, ProgressDataPoint } from '@/types';
import { ScoreCard } from '@/components/dashboard/ScoreCard';
import { SkillRadar } from '@/components/dashboard/SkillRadar';
import { RecentSessions } from '@/components/dashboard/RecentSessions';
import { Recommendations } from '@/components/dashboard/Recommendations';
import { ProgressChart } from '@/components/dashboard/ProgressChart';
import { Phone } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [progress, setProgress] = useState<ProgressDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [dashboardData, progressData] = await Promise.all([
          getDashboard(),
          getProgress(30),
        ]);
        setDashboard(dashboardData);
        setProgress(progressData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const hasData = dashboard && dashboard.total_sessions > 0;

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Track your progress and improve your sales skills
          </p>
        </div>
        <Link
          href="/practice"
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Phone className="w-5 h-5 mr-2" />
          Start Practice Call
        </Link>
      </div>

      {!hasData ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Phone className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            No practice sessions yet
          </h2>
          <p className="text-gray-500 mb-6 max-w-md mx-auto">
            Start your first practice call to begin tracking your progress
            and receiving AI-powered feedback.
          </p>
          <Link
            href="/practice"
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Phone className="w-5 h-5 mr-2" />
            Start Your First Call
          </Link>
        </div>
      ) : (
        <>
          {/* Score Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <ScoreCard
              title="Overall Score"
              score={dashboard.current_overall_score}
              trend={dashboard.score_trend_7_days}
              color="primary"
            />
            <ScoreCard
              title="Sales Skills"
              score={dashboard.current_sales_score}
              color="blue"
            />
            <ScoreCard
              title="Technical Knowledge"
              score={dashboard.current_technical_score}
              color="purple"
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column */}
            <div className="lg:col-span-2 space-y-8">
              {/* Progress Chart */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Progress Over Time
                </h2>
                <ProgressChart data={progress} />
              </div>

              {/* Recent Sessions */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Recent Sessions
                </h2>
                <RecentSessions sessions={dashboard.recent_sessions} />
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-8">
              {/* Skill Radar */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Skill Breakdown
                </h2>
                <SkillRadar skills={dashboard.skill_averages} />
              </div>

              {/* Recommendations */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Focus Areas
                </h2>
                <Recommendations recommendations={dashboard.active_recommendations} />
              </div>

              {/* Stats */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Practice Stats
                </h2>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Total Sessions</span>
                    <span className="font-semibold">{dashboard.total_sessions}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">Practice Time</span>
                    <span className="font-semibold">
                      {dashboard.total_practice_minutes} min
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
