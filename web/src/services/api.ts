import type {
  AdvisorSession, DistillSession, Gate, LensReview, Methodology, Run, RunDetail, Suggestion,
} from '../types'

const BASE = '/api'

function qs(params?: Record<string, string | undefined>): string {
  if (!params) return ''
  const entries = Object.entries(params).filter(([, v]) => v != null && v !== '')
  if (!entries.length) return ''
  return '?' + entries.map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`).join('&')
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`${res.status} ${txt}`)
  }
  return (await res.json()) as T
}

export interface AnswerResult {
  resolved: boolean
  reason: string
  followup: string
  run_done: boolean
  next_gate: (Gate & { step_name?: string; step_intent?: string }) | null
}
export interface AskResult {
  done: boolean
  gate: (Gate & { step_name?: string; step_intent?: string }) | null
  ai_question: string
  gate_response_id?: string
}

export const api = {
  listMethodologies: (p?: { origin?: string; tag?: string; q?: string }) =>
    request<{ methodologies: Methodology[]; total: number }>(`/methodologies${qs(p)}`),
  getMethodology: (id: string) => request<Methodology>(`/methodologies/${id}`),
  createMethodology: (body: Partial<Methodology>) =>
    request<Methodology>('/methodologies', { method: 'POST', body: JSON.stringify(body) }),
  updateMethodology: (id: string, body: Partial<Methodology>) =>
    request<Methodology>(`/methodologies/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  exportMethodology: (id: string) =>
    request<{ id: string; format: string; content: string }>(`/methodologies/${id}/export?format=agent_md`),
  forkMethodology: (id: string) =>
    request<Methodology>(`/methodologies/${id}/fork`, { method: 'POST' }),

  // ── distillation ──
  distillFromMaterials: (body: { materials: string[]; hint?: string; topic?: string }) =>
    request<{ methodology: Methodology }>('/distill/materials', { method: 'POST', body: JSON.stringify(body) }),
  interviewStart: (body: { topic: string; expert_name?: string }) =>
    request<{ session: DistillSession; question: string }>('/distill/interview/start', {
      method: 'POST', body: JSON.stringify(body),
    }),
  interviewGet: (id: string) => request<{ session: DistillSession }>(`/distill/interview/${id}`),
  interviewAnswer: (id: string, answer: string) =>
    request<{ done: boolean; question: string }>(`/distill/interview/${id}/answer`, {
      method: 'POST', body: JSON.stringify({ answer }),
    }),
  interviewSynthesize: (id: string) =>
    request<{ methodology: Methodology }>(`/distill/interview/${id}/synthesize`, { method: 'POST' }),
  suggest: (raw_input: string) =>
    request<{ suggestions: Suggestion[]; mode: string }>('/methodologies/suggest', {
      method: 'POST',
      body: JSON.stringify({ raw_input }),
    }),

  createRun: (body: { methodology_id: string; raw_input: string; title?: string }) =>
    request<RunDetail>('/runs', { method: 'POST', body: JSON.stringify(body) }),
  listRuns: (p?: { methodology_id?: string; status?: string }) =>
    request<{ runs: Run[]; total: number }>(`/runs${qs(p)}`),
  getRun: (id: string) => request<RunDetail>(`/runs/${id}`),
  ask: (id: string) => request<AskResult>(`/runs/${id}/ask`, { method: 'POST' }),
  answer: (id: string, gate_id: string, answer: string) =>
    request<AnswerResult>(`/runs/${id}/answer`, { method: 'POST', body: JSON.stringify({ gate_id, answer }) }),
  synthesize: (id: string) => request<RunDetail>(`/runs/${id}/synthesize`, { method: 'POST' }),
  recordOutcome: (id: string, body: { usefulness: number; adopted: boolean; metric_values?: Record<string, unknown>; note?: string }) =>
    request<{ outcome: unknown }>(`/runs/${id}/outcome`, { method: 'POST', body: JSON.stringify(body) }),

  // ── lens (透镜诊断) ──
  lensDiagnose: (body: { methodology_id: string; material: string; title?: string }) =>
    request<{ review: LensReview }>('/lens', { method: 'POST', body: JSON.stringify(body) }),
  listLens: (p?: { methodology_id?: string }) =>
    request<{ reviews: LensReview[]; total: number }>(`/lens${qs(p)}`),
  getLens: (id: string) => request<{ review: LensReview }>(`/lens/${id}`),

  // ── advisor (顾问陪练) ──
  advisorStart: (body: { methodology_id: string; topic?: string }) =>
    request<{ session: AdvisorSession }>('/advisor/start', { method: 'POST', body: JSON.stringify(body) }),
  advisorMessage: (id: string, content: string) =>
    request<{ session: AdvisorSession }>(`/advisor/${id}/message`, { method: 'POST', body: JSON.stringify({ content }) }),
  getAdvisor: (id: string) => request<{ session: AdvisorSession }>(`/advisor/${id}`),

  // ── OPC bindings ──
  getBinding: (role: string) => request<{ agent_role: string; methodology_id: string | null }>(`/bindings/${role}`),
  setBinding: (role: string, methodology_id: string) =>
    request<{ agent_role: string; methodology_id: string }>(`/bindings/${role}`, {
      method: 'PUT', body: JSON.stringify({ methodology_id }),
    }),
}
