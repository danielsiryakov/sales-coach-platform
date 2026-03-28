export type CallType = 'cold_call' | 'warm_lead' | 'renewal' | 'cross_sell' | 'claims' | 'review';
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type SessionStatus = 'pending' | 'active' | 'completed' | 'analyzing' | 'scored' | 'error';

export interface ScenarioTemplate {
  id: number;
  name: string;
  description: string | null;
  call_type: CallType;
  objectives: string[] | null;
  difficulty_level: DifficultyLevel;
  estimated_duration_minutes: number;
}

export interface BusinessContext {
  id: number;
  trade_name: string;
  trade_code: string;
  description: string | null;
  typical_operations: string[] | null;
  common_risks: string[] | null;
  required_coverages: string[] | null;
}

export interface SessionCreateRequest {
  scenario_template_id: number;
  business_context_id: number;
  difficulty_level: DifficultyLevel;
  voice_id?: string;
}

export interface Session {
  id: number;
  session_uuid: string;
  status: SessionStatus;
  persona_name: string | null;
  persona_company: string | null;
  scenario_name: string | null;
  business_context: string | null;
  difficulty_level: DifficultyLevel;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  created_at: string;
  overall_score?: number | null;
  sales_skills_score?: number | null;
  technical_knowledge_score?: number | null;
}

export interface SessionDetail extends Session {
  persona_details: Record<string, any> | null;
  system_prompt: string | null;
  voice_id: string;
}

export interface TranscriptEntry {
  speaker: 'user' | 'ai';
  text: string;
  timestamp_ms: number;
}

export interface SkillScore {
  skill_name: string;
  skill_category: 'sales' | 'technical';
  score: number;
  weight: number;
  trend_vs_previous: number | null;
  evidence_quotes: string[] | null;
}

export interface ScoreDetail {
  session_uuid: string;
  overall_score: number;
  sales_skills_score: number;
  technical_knowledge_score: number;
  performance_level: string;
  skill_evaluations: SkillScore[];
  top_strengths: Array<{
    skill: string;
    evidence_quote: string;
    score: number;
  }> | null;
  improvement_areas: Array<{
    skill: string;
    evidence_quote: string;
    recommendation: string;
  }> | null;
  coaching_feedback: string | null;
  analyzed_at: string;
}

export interface Recommendation {
  id: number;
  skill_name: string;
  priority: number;
  recommendation: string;
  example_phrases: string[] | null;
  practice_tips: string[] | null;
  is_active: boolean;
}

export interface DashboardSummary {
  total_sessions: number;
  total_practice_minutes: number;
  current_overall_score: number | null;
  current_sales_score: number | null;
  current_technical_score: number | null;
  score_trend_7_days: number | null;
  recent_sessions: Array<{
    session_uuid: string;
    status: string;
    persona_name: string | null;
    created_at: string;
    duration_seconds: number | null;
    overall_score?: number;
  }>;
  skill_averages: Record<string, number>;
  active_recommendations: Recommendation[];
}

export interface ProgressDataPoint {
  date: string;
  overall_score: number;
  sales_score: number;
  technical_score: number;
}

// WebSocket message types
export interface WSMessage {
  type: string;
  [key: string]: any;
}

export interface WSAudioMessage extends WSMessage {
  type: 'audio';
  audio: string; // base64
}

export interface WSTranscriptMessage extends WSMessage {
  type: 'transcript';
  speaker: 'user' | 'ai';
  text: string;
  timestamp_ms: number;
}

export interface WSErrorMessage extends WSMessage {
  type: 'error';
  message: string;
}
