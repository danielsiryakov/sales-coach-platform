import type {
  ScenarioTemplate,
  BusinessContext,
  Session,
  SessionDetail,
  SessionCreateRequest,
  ScoreDetail,
  DashboardSummary,
  ProgressDataPoint,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  console.log('[API] Fetching:', url);

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    console.log('[API] Response status:', response.status);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('[API] Error response:', error);
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    console.log('[API] Success, got data');
    return data;
  } catch (err) {
    console.error('[API] Fetch failed:', err);
    throw err;
  }
}

// Sessions
export async function createSession(data: SessionCreateRequest): Promise<SessionDetail> {
  return fetchApi<SessionDetail>('/sessions/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listSessions(status?: string): Promise<Session[]> {
  const params = status ? `?status=${status}` : '';
  return fetchApi<Session[]>(`/sessions/${params}`);
}

export async function getSession(sessionUuid: string): Promise<SessionDetail> {
  return fetchApi<SessionDetail>(`/sessions/${sessionUuid}`);
}

export async function deleteSession(sessionUuid: string): Promise<void> {
  await fetchApi(`/sessions/${sessionUuid}`, { method: 'DELETE' });
}

// Scenarios
export async function listScenarioTemplates(callType?: string): Promise<ScenarioTemplate[]> {
  const params = callType ? `?call_type=${callType}` : '';
  return fetchApi<ScenarioTemplate[]>(`/scenarios/templates${params}`);
}

export async function listBusinessContexts(): Promise<BusinessContext[]> {
  return fetchApi<BusinessContext[]>('/scenarios/business-contexts');
}

// Analytics
export async function getSessionScore(sessionUuid: string): Promise<ScoreDetail> {
  return fetchApi<ScoreDetail>(`/analytics/session/${sessionUuid}/score`);
}

export async function getDashboard(): Promise<DashboardSummary> {
  return fetchApi<DashboardSummary>('/analytics/dashboard');
}

export async function getProgress(days: number = 30): Promise<ProgressDataPoint[]> {
  return fetchApi<ProgressDataPoint[]>(`/analytics/progress?days=${days}`);
}

export async function dismissRecommendation(recId: number): Promise<void> {
  await fetchApi(`/analytics/recommendations/${recId}/dismiss`, { method: 'POST' });
}

// Recordings
export async function getTranscript(
  sessionUuid: string
): Promise<{ transcript: any[]; transcript_text: string }> {
  return fetchApi(`/recordings/${sessionUuid}/transcript`);
}

// Generate coaching feedback on demand
export async function generateCoachingFeedback(
  sessionUuid: string
): Promise<{ session_uuid: string; coaching_feedback: string }> {
  return fetchApi(`/analytics/session/${sessionUuid}/generate-feedback`, {
    method: 'POST',
  });
}
