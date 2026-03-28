'use client';

import { cn, getScoreColor, getPerformanceLevel } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreCardProps {
  title: string;
  score: number | null;
  trend?: number | null;
  color?: 'primary' | 'blue' | 'purple' | 'green';
}

const colorClasses = {
  primary: 'bg-primary-50 border-primary-200',
  blue: 'bg-blue-50 border-blue-200',
  purple: 'bg-purple-50 border-purple-200',
  green: 'bg-green-50 border-green-200',
};

export function ScoreCard({ title, score, trend, color = 'primary' }: ScoreCardProps) {
  const displayScore = score !== null ? Math.round(score) : '--';
  const level = score !== null ? getPerformanceLevel(score) : 'No data';

  return (
    <div className={cn(
      'rounded-xl border p-6',
      colorClasses[color]
    )}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {trend !== null && trend !== undefined && (
          <div className={cn(
            'flex items-center text-sm',
            trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-400'
          )}>
            {trend > 0 ? (
              <TrendingUp className="w-4 h-4 mr-1" />
            ) : trend < 0 ? (
              <TrendingDown className="w-4 h-4 mr-1" />
            ) : (
              <Minus className="w-4 h-4 mr-1" />
            )}
            {trend > 0 ? '+' : ''}{Math.round(trend)}
          </div>
        )}
      </div>
      <div className="flex items-baseline">
        <span className={cn(
          'text-4xl font-bold',
          score !== null ? getScoreColor(score) : 'text-gray-400'
        )}>
          {displayScore}
        </span>
        {score !== null && (
          <span className="ml-2 text-sm text-gray-500">/100</span>
        )}
      </div>
      <div className="mt-2 text-sm text-gray-500">{level}</div>
    </div>
  );
}
