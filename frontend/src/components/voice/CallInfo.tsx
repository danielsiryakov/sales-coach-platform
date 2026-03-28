'use client';

import type { SessionDetail } from '@/types';
import { Building, User, Target, AlertTriangle, Briefcase } from 'lucide-react';

interface CallInfoProps {
  session: SessionDetail;
}

export function CallInfo({ session }: CallInfoProps) {
  const persona = session.persona_details || {};

  return (
    <div className="space-y-6 text-sm">
      {/* Prospect Info */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Prospect
        </h3>
        <div className="space-y-3">
          <div className="flex items-start">
            <User className="w-4 h-4 text-gray-500 mr-2 mt-0.5" />
            <div>
              <p className="text-white font-medium">{session.persona_name}</p>
              <p className="text-gray-400">{persona.trade || session.business_context}</p>
            </div>
          </div>
          <div className="flex items-start">
            <Building className="w-4 h-4 text-gray-500 mr-2 mt-0.5" />
            <div>
              <p className="text-white">{session.persona_company}</p>
              {persona.business_details && (
                <p className="text-gray-400">
                  ${persona.business_details.annual_revenue?.toLocaleString()} revenue
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Scenario */}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Scenario
        </h3>
        <div className="flex items-start">
          <Target className="w-4 h-4 text-gray-500 mr-2 mt-0.5" />
          <div>
            <p className="text-white">{session.scenario_name}</p>
            <p className="text-gray-400 capitalize">
              {session.difficulty_level} difficulty
            </p>
          </div>
        </div>
      </div>

      {/* Personality Traits */}
      {persona.traits && persona.traits.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Personality
          </h3>
          <div className="flex flex-wrap gap-2">
            {persona.traits.map((trait: string, i: number) => (
              <span
                key={i}
                className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs"
              >
                {trait}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Objections to expect */}
      {persona.objections && persona.objections.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Expected Objections
          </h3>
          <div className="space-y-2">
            {persona.objections.map((objection: string, i: number) => (
              <p
                key={i}
                className="text-gray-400 text-xs italic border-l-2 border-yellow-600 pl-2"
              >
                "{objection}"
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Business Details */}
      {persona.business_details && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Business Details
          </h3>
          <div className="space-y-2 text-gray-400">
            <div className="flex justify-between">
              <span>Employees</span>
              <span className="text-white">{persona.business_details.employees}</span>
            </div>
            <div className="flex justify-between">
              <span>Years in Business</span>
              <span className="text-white">{persona.business_details.years_in_business}</span>
            </div>
            <div className="flex justify-between">
              <span>Uses Subs</span>
              <span className="text-white">
                {persona.business_details.uses_subcontractors ? 'Yes' : 'No'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="bg-primary-900/30 border border-primary-800 rounded-lg p-4">
        <h3 className="text-xs font-semibold text-primary-400 uppercase tracking-wider mb-2">
          Quick Tips
        </h3>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>- Listen actively and acknowledge their concerns</li>
          <li>- Ask open-ended questions to understand needs</li>
          <li>- Reference their specific trade and risks</li>
          <li>- Handle objections with empathy first</li>
        </ul>
      </div>
    </div>
  );
}
