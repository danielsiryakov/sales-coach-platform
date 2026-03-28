'use client';

import { dismissRecommendation } from '@/lib/api';
import { X, Lightbulb } from 'lucide-react';
import { useState } from 'react';
import type { Recommendation } from '@/types';

interface RecommendationsProps {
  recommendations: Recommendation[];
}

export function Recommendations({ recommendations }: RecommendationsProps) {
  const [dismissed, setDismissed] = useState<number[]>([]);

  const handleDismiss = async (id: number) => {
    try {
      await dismissRecommendation(id);
      setDismissed([...dismissed, id]);
    } catch (err) {
      console.error('Failed to dismiss recommendation:', err);
    }
  };

  const activeRecs = recommendations.filter(r => !dismissed.includes(r.id));

  if (activeRecs.length === 0) {
    return (
      <div className="text-center text-gray-400 py-6">
        <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No recommendations yet</p>
        <p className="text-sm">Complete more calls to get personalized tips</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activeRecs.map((rec) => (
        <div
          key={rec.id}
          className="relative bg-yellow-50 border border-yellow-200 rounded-lg p-4"
        >
          <button
            onClick={() => handleDismiss(rec.id)}
            className="absolute top-2 right-2 text-yellow-600 hover:text-yellow-800"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-yellow-200 text-yellow-800 text-xs font-bold">
                {rec.priority}
              </span>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-yellow-800">
                {rec.skill_name}
              </p>
              <p className="mt-1 text-sm text-yellow-700">
                {rec.recommendation}
              </p>
              {rec.example_phrases && rec.example_phrases.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-yellow-600">
                    Try saying:
                  </p>
                  <p className="text-xs text-yellow-700 italic">
                    "{rec.example_phrases[0]}"
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
