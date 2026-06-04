export interface Principle { title: string; detail: string }
export interface Step { id: string; name: string; intent?: string; guidance?: string }
export interface Gate { id: string; step_id: string; question: string; why?: string; pass_criteria?: string }
export interface AntiPattern { name: string; symptom: string; fix: string }
export interface Artifact { name: string; format?: string; template?: string }
export interface Metric { name: string; how_to_measure?: string; target?: string }
export interface Trigger { scenarios?: string[]; keywords?: string[] }
export interface Applicability { when_to_use?: string[]; when_not_to_use?: string[] }
export interface Example { kind: 'positive' | 'negative'; title: string; content: string }
export interface Provenance { source_type?: string; origin?: string; note?: string; forked_from?: string | null }
export interface Related { slug: string; relation: string; note?: string }

export interface Methodology {
  id: string
  slug: string
  name: string
  summary: string
  trigger: Trigger
  principles: Principle[]
  steps: Step[]
  gates: Gate[]
  anti_patterns: AntiPattern[]
  artifacts: Artifact[]
  metrics: Metric[]
  applicability: Applicability
  examples: Example[]
  provenance: Provenance
  related: Related[]
  origin: 'builtin' | 'custom'
  status: string
  version: number
  run_count: number
  avg_artifact_score: number | null
  tags: string[]
  created_at: string
  updated_at: string
}

export interface GateResponse {
  id: string
  run_id: string
  gate_id: string
  step_id: string
  ai_question: string
  user_answer: string
  resolved: boolean
}

export interface Run {
  id: string
  methodology_id: string
  methodology_version: number
  title: string
  raw_input: string
  status: 'created' | 'in_progress' | 'completed' | 'abandoned'
  current_step_index: number
  artifact_md: string
  artifact_score: ArtifactScore | null
  created_at: string
  completed_at: string | null
}

export interface ArtifactScore {
  phase: string
  total: number
  dimensions: Record<string, number>
  stats: Record<string, unknown>
}

export interface RunDetail {
  run: Run
  gate_responses: GateResponse[]
  methodology: { id: string; slug: string; name: string; steps: Step[]; gates: Gate[]; artifacts: Artifact[] } | null
}

export interface Suggestion { id: string; slug: string; name: string; score: number }

export interface GateFinding { gate_id: string; question: string; verdict: 'pass' | 'concern' | 'fail'; evidence: string; suggestion: string }
export interface LensDiagnosis {
  overall: string
  score: { total: number } | null
  gate_findings: GateFinding[]
  anti_pattern_hits: { name: string; evidence: string }[]
  strengths: string[]
  top_fixes: string[]
}
export interface LensReview {
  id: string
  methodology_id: string
  methodology_name: string
  title: string
  material: string
  diagnosis: LensDiagnosis
  score: { total: number } | null
  created_at: string
}

export interface AdvisorMessage { role: 'user' | 'assistant'; content: string }
export interface AdvisorSession {
  id: string
  methodology_id: string
  methodology_name: string
  topic: string
  messages: AdvisorMessage[]
  status: string
}

export interface DistillSession {
  id: string
  mode: 'interview' | 'materials'
  topic: string
  expert_name: string
  status: 'in_progress' | 'completed'
  transcript: { question: string; answer: string }[]
  materials: string[]
  draft_methodology_id: string | null
}
