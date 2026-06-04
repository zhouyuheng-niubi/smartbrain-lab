import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ScanSearch, CheckCircle2, AlertTriangle, XCircle, Wand2 } from 'lucide-react'
import { api } from '../services/api'
import type { LensReview, Methodology } from '../types'
import { useUI } from '../store'

const VERDICT: Record<string, { color: string; Icon: typeof CheckCircle2; label: string }> = {
  pass: { color: 'var(--good)', Icon: CheckCircle2, label: '通过' },
  concern: { color: 'var(--warn)', Icon: AlertTriangle, label: '存疑' },
  fail: { color: '#f87171', Icon: XCircle, label: '不符' },
}

export default function Lens() {
  const notify = useUI((s) => s.notify)
  const [sp] = useSearchParams()
  const [methods, setMethods] = useState<Methodology[]>([])
  const [mid, setMid] = useState(sp.get('methodology') || '')
  const [title, setTitle] = useState('')
  const [material, setMaterial] = useState('')
  const [review, setReview] = useState<LensReview | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.listMethodologies().then((d) => {
      setMethods(d.methodologies)
      if (!mid && d.methodologies.length) setMid(d.methodologies[0].id)
    }).catch((e) => notify(String(e), 'error'))
  }, [])

  const diagnose = async () => {
    if (!mid) return notify('先选一套方法论', 'error')
    if (!material.trim()) return notify('先粘贴要诊断的材料', 'error')
    setBusy(true)
    try {
      const r = await api.lensDiagnose({ methodology_id: mid, material, title })
      setReview(r.review)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  const d = review?.diagnosis

  return (
    <div style={{ maxWidth: 980, margin: '0 auto' }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 10 }}>
        <ScanSearch color="var(--primary)" /> 透镜诊断
      </h1>
      <p className="muted" style={{ marginBottom: 20 }}>戴上一套方法论这副眼镜，给一份现成的材料/决策做体检</p>

      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>用哪套方法论诊断</div>
            <select className="input" value={mid} onChange={(e) => setMid(e.target.value)}>
              {methods.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>材料标题（可选）</div>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="例如：销售看板方案 v1" />
          </div>
        </div>
        <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>被诊断的材料（粘贴一份方案/需求/决策…）</div>
        <textarea className="textarea" rows={6} value={material} onChange={(e) => setMaterial(e.target.value)}
          placeholder="把要体检的内容粘进来…" />
        <button className="btn btn-primary" style={{ marginTop: 12 }} disabled={busy} onClick={diagnose}>
          <Wand2 size={16} /> {busy ? '诊断中…' : '开始诊断'}
        </button>
      </div>

      {d && (
        <div className="card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 12 }}>
            {review?.score?.total != null && (
              <span style={{ fontSize: 30, fontWeight: 800, color: 'var(--primary)' }}>{review.score.total}</span>
            )}
            <div style={{ fontSize: 15, fontWeight: 600 }}>{d.overall}</div>
          </div>

          {d.top_fixes?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>最该先改的</div>
              <ol style={{ paddingLeft: 20, lineHeight: 1.8 }}>{d.top_fixes.map((x, i) => <li key={i}>{x}</li>)}</ol>
            </div>
          )}

          <div style={{ fontWeight: 700, marginBottom: 8 }}>逐决策闸门诊断</div>
          {d.gate_findings?.map((g, i) => {
            const v = VERDICT[g.verdict] || VERDICT.concern
            return (
              <div key={i} className="card" style={{ padding: 12, marginBottom: 8, background: 'var(--bg)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <v.Icon size={16} color={v.color} />
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{g.question}</span>
                  <span className="chip" style={{ marginLeft: 'auto', borderColor: v.color, color: v.color }}>{v.label}</span>
                </div>
                {g.evidence && <div className="muted" style={{ fontSize: 13, marginBottom: 2 }}>依据：{g.evidence}</div>}
                {g.suggestion && <div style={{ fontSize: 13 }}>建议：{g.suggestion}</div>}
              </div>
            )
          })}

          {d.anti_pattern_hits?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 6, color: '#f87171' }}>命中的反模式</div>
              {d.anti_pattern_hits.map((a, i) => (
                <div key={i} style={{ fontSize: 13, marginBottom: 4 }}>⚠️ <b>{a.name}</b>：{a.evidence}</div>
              ))}
            </div>
          )}

          {d.strengths?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 6, color: 'var(--good)' }}>做得好的地方</div>
              {d.strengths.map((s, i) => <div key={i} style={{ fontSize: 13, marginBottom: 4 }}>✅ {s}</div>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
