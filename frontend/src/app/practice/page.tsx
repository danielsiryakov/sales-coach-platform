'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { listScenarioTemplates, listBusinessContexts, createSession } from '@/lib/api';
import type { ScenarioTemplate, BusinessContext, DifficultyLevel } from '@/types';
import { Phone, Briefcase, Target, Gauge, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

const DIFFICULTY_OPTIONS: { value: DifficultyLevel; label: string; description: string }[] = [
  { value: 'beginner', label: 'Beginner', description: 'Friendly prospect, few objections' },
  { value: 'intermediate', label: 'Intermediate', description: 'Balanced challenge, 1-2 objections' },
  { value: 'advanced', label: 'Advanced', description: 'Skeptical prospect, multiple objections' },
  { value: 'expert', label: 'Expert', description: 'Difficult prospect, complex objections' },
];

const VOICE_OPTIONS = [
  { id: 'Rex', label: 'Rex', description: 'Male, professional' },
  { id: 'Leo', label: 'Leo', description: 'Male, friendly' },
  { id: 'Eve', label: 'Eve', description: 'Female, professional' },
  { id: 'Ara', label: 'Ara', description: 'Female, warm' },
];

export default function PracticeSetupPage() {
  const router = useRouter();
  const [scenarios, setScenarios] = useState<ScenarioTemplate[]>([]);
  const [contexts, setContexts] = useState<BusinessContext[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null);
  const [selectedContext, setSelectedContext] = useState<number | null>(null);
  const [difficulty, setDifficulty] = useState<DifficultyLevel>('intermediate');
  const [voice, setVoice] = useState('Rex');

  useEffect(() => {
    async function loadData() {
      console.log('[Practice] Loading data...');
      try {
        const [scenariosData, contextsData] = await Promise.all([
          listScenarioTemplates(),
          listBusinessContexts(),
        ]);
        console.log('[Practice] Loaded scenarios:', scenariosData.length);
        console.log('[Practice] Loaded contexts:', contextsData.length);
        setScenarios(scenariosData);
        setContexts(contextsData);

        // Pre-select first options
        if (scenariosData.length > 0) setSelectedScenario(scenariosData[0].id);
        if (contextsData.length > 0) setSelectedContext(contextsData[0].id);
      } catch (err) {
        console.error('[Practice] Error loading data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load options');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleStartCall = async () => {
    if (!selectedScenario || !selectedContext) return;

    setCreating(true);
    setError(null);

    try {
      const session = await createSession({
        scenario_template_id: selectedScenario,
        business_context_id: selectedContext,
        difficulty_level: difficulty,
        voice_id: voice,
      });

      router.push(`/practice/${session.session_uuid}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
      setCreating(false);
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
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Start Practice Call</h1>
        <p className="text-gray-500 mt-1">
          Configure your practice scenario and begin
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}

      <div className="space-y-8">
        {/* Scenario Selection */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Target className="w-5 h-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Call Scenario</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => setSelectedScenario(scenario.id)}
                className={cn(
                  'p-4 rounded-lg border text-left transition-all',
                  selectedScenario === scenario.id
                    ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <p className="font-medium text-gray-900">{scenario.name}</p>
                <p className="text-sm text-gray-500 mt-1">{scenario.description}</p>
                <div className="flex items-center mt-2 text-xs text-gray-400">
                  <span className="capitalize">{scenario.call_type.replace('_', ' ')}</span>
                  <span className="mx-2">-</span>
                  <span>{scenario.estimated_duration_minutes} min</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Business Context Selection */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Briefcase className="w-5 h-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Prospect Trade</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {contexts.map((context) => (
              <button
                key={context.id}
                onClick={() => setSelectedContext(context.id)}
                className={cn(
                  'p-3 rounded-lg border text-left transition-all',
                  selectedContext === context.id
                    ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <p className="font-medium text-gray-900 text-sm">{context.trade_name}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Difficulty Selection */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Gauge className="w-5 h-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Difficulty Level</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {DIFFICULTY_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setDifficulty(option.value)}
                className={cn(
                  'p-3 rounded-lg border text-center transition-all',
                  difficulty === option.value
                    ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <p className="font-medium text-gray-900">{option.label}</p>
                <p className="text-xs text-gray-500 mt-1">{option.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Voice Selection */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <Phone className="w-5 h-5 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Prospect Voice</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {VOICE_OPTIONS.map((option) => (
              <button
                key={option.id}
                onClick={() => setVoice(option.id)}
                className={cn(
                  'p-3 rounded-lg border text-center transition-all',
                  voice === option.id
                    ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <p className="font-medium text-gray-900">{option.label}</p>
                <p className="text-xs text-gray-500">{option.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Start Button */}
        <div className="flex justify-end">
          <button
            onClick={handleStartCall}
            disabled={creating || !selectedScenario || !selectedContext}
            className={cn(
              'flex items-center px-8 py-4 rounded-lg font-semibold text-lg transition-all',
              creating || !selectedScenario || !selectedContext
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            )}
          >
            {creating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3" />
                Setting up...
              </>
            ) : (
              <>
                Start Practice Call
                <ChevronRight className="w-5 h-5 ml-2" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
