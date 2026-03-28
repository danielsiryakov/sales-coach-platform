'use client';

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';

interface SkillRadarProps {
  skills: Record<string, number>;
}

export function SkillRadar({ skills }: SkillRadarProps) {
  if (!skills || Object.keys(skills).length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        No skill data available
      </div>
    );
  }

  // Transform skills object to chart data
  const data = Object.entries(skills).map(([name, score]) => ({
    skill: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    score: Math.round(score),
    fullMark: 100,
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="skill"
            tick={{ fontSize: 10, fill: '#6b7280' }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: '#9ca3af' }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#0ea5e9"
            fill="#0ea5e9"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
