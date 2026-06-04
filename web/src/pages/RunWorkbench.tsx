import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ArrowLeft, CheckCircle2, Circle, Wand2 } from 'lucide-react'
import { api, type AskResult } from '../services/api'
import type { RunDetail } from '../types'
import { useUI } from '../store'

export default function RunWorkbench() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const notify = useUI((s) => s.notify)
  const [detail, setDetail] = useState<RunDetail | null>(null)
  const [current, setCurrent] = useState<AskResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [answer, setAnswer] = useState('')

  const refresh = async () => { const d = await api.getRun(id); setDetail(d); return d }
  const pull = async () => { const a = await api.ask(id); setCurrent(a); return a }

  useEffect(() => {
    (async () => {
      try {
        const d = await refresh()
        if (d.run.status === 'in_progress') await pull()
      } catch (e) { notify(String(e), 'error') }
    })()
  }, [id])

  if (!detail) return <div className="muted">加载中…</div>
  const { run, methodology, gate_responses } = detail
  const resolvedIds = new Set(gate_responses.filter((g) => g.resolved).map((g) => g.gate_id))
  const steps = methodology?.steps || []
  const gates = methodology?.gates || []

  const submit = async () => {
    if (!current?.gate || !answer.trim()) return
    setBusy(true)
    try {
      const res = await api.answer(id, current.gate.id, answer)
      setAnswer('')
      notify(res.resolved ? `✓ ${res.reason || '已通过'}` : `继续：${res.followup || res.reason}`, res.resolved ? 'good' : 'info')
      await refresh()
      if (res.run_done) setCurrent({ done: true, gate: null, ai_question: '' })
      else await pull()
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  const synthesize = async () => {
    setBusy(true)
    try { setDetail(await api.synthesize(id)); notify('已合成结构化产出物', 'good') }
    catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  const score = run.artifact_score

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto' }}>
      <button className="btn" onClick={() => nav('/')} style={{ marginBottom: 16 }}><ArrowLeft size={16} /> 方法论库</button>
      <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>{methodology?.name} · 试跑</h1>
      <p className="muted" style={{ marginBottom: 20 }}>{run.title}</p>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 1fr', gap: 18, alignItems: 'start' }}>
        {/* 左：原始需求 + 步骤进度 */}
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>原始需求</div>
          <div className="muted" style={{ fontSize: 13, lineHeight: 1.6, marginBottom: 16, whiteSpace: 'pre-wrap' }}>{run.raw_input}</div>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>步骤进度</div>
          {steps.map((s, i) => {
            const sGates = gates.filter((g) => g.step_id === s.id)
            const done = sGates.length > 0 && sGates.every((g) => resolvedIds.has(g.id))
            const active = i === run.current_step_index && run.status === 'in_progress'
            return (
              <div key={s.id} style={{ display: 'flex', gap: 8, alignItems: 'center', padding: '6px 0', opacity: done || active ? 1 : 0.6 }}>
                {done ? <CheckCircle2 size={16} color="var(--good)" /> : <Circle size={16} color={active ? 'var(--primary)' : 'var(--muted)'} />}
                <span style={{ fontSize: 13, color: active ? 'var(--primary)' : 'var(--text)', fontWeight: active ? 700 : 400 }}>{s.name}</span>
              </div>
            )
          })}
        </div>

        {/* 中：当前 gate 问答 */}
        <div>
          {run.status === 'completed' ? (
            <div className="card" style={{ padding: 20, textAlign: 'center' }}>
              <CheckCircle2 size={32} color="var(--good)" style={{ margin: '0 auto 8px' }} />
              <div style={{ fontWeight: 700 }}>试跑完成</div>
              <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>产出物已生成，去 <a style={{ color: 'var(--primary)' }} onClick={() => nav('/runs')}>试跑历史</a> 记录效果</div>
            </div>
          ) : current?.done ? (
            <div className="card" style={{ padding: 20, textAlign: 'center' }}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>所有决策闸门已通过 🎉</div>
              <button className="btn btn-primary" disabled={busy} onClick={synthesize}><Wand2 size={16} /> 合成结构化产出物</button>
            </div>
          ) : current?.gate ? (
            <div className="card" style={{ padding: 20 }}>
              {current.gate.step_name && <div className="chip" style={{ marginBottom: 12 }}>{current.gate.step_name}</div>}
              <div style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.6, marginBottom: 14 }}>{current.ai_question}</div>
              <textarea className="textarea" rows={6} placeholder="在这里作答…" value={answer} disabled={busy} onChange={(e) => setAnswer(e.target.value)} />
              <button className="btn btn-primary" style={{ marginTop: 12 }} disabled={busy || !answer.trim()} onClick={submit}>
                {busy ? '判定中…' : '提交作答'}
              </button>
            </div>
          ) : (
            <div className="muted">准备中…</div>
          )}
        </div>

        {/* 右：产出物预览 + 质量分 */}
        <div className="card" style={{ padding: 18, minHeight: 200 }}>
          <div style={{ fontWeight: 700, marginBottom: 10 }}>结构化产出物</div>
          {score && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 28, fontWeight: 800, color: 'var(--primary)' }}>{score.total}</span>
                <span className="muted" style={{ fontSize: 12 }}>/ 10 质量分</span>
              </div>
              {Object.entries(score.dimensions).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span className="muted" style={{ fontSize: 11, width: 96 }}>{k}</span>
                  <div style={{ flex: 1, height: 6, background: 'var(--bg)', borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ width: `${(v / 10) * 100}%`, height: '100%', background: 'linear-gradient(90deg, var(--primary), var(--accent))' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
          {run.artifact_md
            ? <div className="markdown"><Markdown remarkPlugins={[remarkGfm]}>{run.artifact_md}</Markdown></div>
            : <div className="muted" style={{ fontSize: 13 }}>走完所有决策闸门后，这里会生成结构化拆解书。</div>}
        </div>
      </div>
    </div>
  )
}
