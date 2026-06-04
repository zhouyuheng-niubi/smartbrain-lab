import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FlaskConical, FileText, MessagesSquare, Plus, Trash2, Send, Wand2 } from 'lucide-react'
import { api } from '../services/api'
import { useUI } from '../store'

export default function Distill() {
  const nav = useNavigate()
  const notify = useUI((s) => s.notify)
  const [tab, setTab] = useState<'materials' | 'interview'>('materials')
  const [busy, setBusy] = useState(false)

  // ── materials mode ──
  const [topic, setTopic] = useState('')
  const [hint, setHint] = useState('')
  const [materials, setMaterials] = useState<string[]>([''])

  const distillMaterials = async () => {
    const mats = materials.map((s) => s.trim()).filter(Boolean)
    if (!mats.length) return notify('至少粘贴一段真实材料', 'error')
    setBusy(true)
    try {
      const r = await api.distillFromMaterials({ materials: mats, hint, topic })
      notify('已蒸馏出草稿，请审定后发布', 'good')
      nav(`/methodology/${r.methodology.id}/edit`)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  // ── interview mode ──
  const [iTopic, setITopic] = useState('')
  const [expert, setExpert] = useState('')
  const [sid, setSid] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [qaCount, setQaCount] = useState(0)
  const [done, setDone] = useState(false)

  const startInterview = async () => {
    if (!iTopic.trim()) return notify('填写访谈主题', 'error')
    setBusy(true)
    try {
      const r = await api.interviewStart({ topic: iTopic, expert_name: expert })
      setSid(r.session.id); setQuestion(r.question); setQaCount(0); setDone(false)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }
  const submitAnswer = async () => {
    if (!sid || !answer.trim()) return
    setBusy(true)
    try {
      const r = await api.interviewAnswer(sid, answer)
      setAnswer(''); setQaCount((c) => c + 1)
      if (r.done) { setDone(true); setQuestion('') } else setQuestion(r.question)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }
  const synth = async () => {
    if (!sid) return
    setBusy(true)
    try {
      const r = await api.interviewSynthesize(sid)
      notify('已合成方法论草稿，请审定', 'good')
      nav(`/methodology/${r.methodology.id}/edit`)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  return (
    <div style={{ maxWidth: 880, margin: '0 auto' }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 10 }}>
        <FlaskConical color="var(--accent)" /> 蒸馏
      </h1>
      <p className="muted" style={{ marginBottom: 20 }}>把资深人脑里的隐性套路，提炼成可复用的方法论数字资产（产出为草稿，审定后发布）</p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button className="btn" onClick={() => setTab('materials')} style={{ borderColor: tab === 'materials' ? 'var(--primary)' : 'var(--border)' }}>
          <FileText size={16} /> 从真实材料提炼
        </button>
        <button className="btn" onClick={() => setTab('interview')} style={{ borderColor: tab === 'interview' ? 'var(--primary)' : 'var(--border)' }}>
          <MessagesSquare size={16} /> 专家访谈式提炼
        </button>
      </div>

      {tab === 'materials' && (
        <div className="card" style={{ padding: 20 }}>
          <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>主题（这套套路是关于什么的）</div>
          <input className="input" style={{ marginBottom: 12 }} placeholder="例如：代码评审 / 需求拆解 / 线上事故复盘" value={topic} onChange={(e) => setTopic(e.target.value)} />
          <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>提示（可选，告诉 AI 重点提炼什么）</div>
          <input className="input" style={{ marginBottom: 12 }} placeholder="例如：提炼老张评审时最看重的判断" value={hint} onChange={(e) => setHint(e.target.value)} />
          <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>真实材料（粘贴几份优秀样例：评审记录 / 复盘 / 方案…）</div>
          {materials.map((mat, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <textarea className="textarea" rows={3} placeholder={`材料 ${i + 1}`} value={mat}
                onChange={(e) => setMaterials(materials.map((x, idx) => (idx === i ? e.target.value : x)))} />
              {materials.length > 1 && (
                <button className="btn" onClick={() => setMaterials(materials.filter((_, idx) => idx !== i))}><Trash2 size={14} /></button>
              )}
            </div>
          ))}
          <button className="btn" onClick={() => setMaterials([...materials, ''])} style={{ marginBottom: 14 }}><Plus size={14} /> 再加一段</button>
          <div>
            <button className="btn btn-primary" disabled={busy} onClick={distillMaterials}>
              <Wand2 size={16} /> {busy ? '蒸馏中…' : '开始蒸馏'}
            </button>
          </div>
        </div>
      )}

      {tab === 'interview' && (
        <div className="card" style={{ padding: 20 }}>
          {!sid ? (
            <>
              <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>访谈主题</div>
              <input className="input" style={{ marginBottom: 12 }} placeholder="例如：如何做技术选型" value={iTopic} onChange={(e) => setITopic(e.target.value)} />
              <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>受访专家（可选，用于标注出处）</div>
              <input className="input" style={{ marginBottom: 14 }} placeholder="例如：张三" value={expert} onChange={(e) => setExpert(e.target.value)} />
              <button className="btn btn-primary" disabled={busy} onClick={startInterview}><MessagesSquare size={16} /> 开始访谈</button>
            </>
          ) : done ? (
            <div style={{ textAlign: 'center', padding: 12 }}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>访谈完成，已采集 {qaCount} 个回答 🎉</div>
              <button className="btn btn-primary" disabled={busy} onClick={synth}><Wand2 size={16} /> 合成方法论草稿</button>
            </div>
          ) : (
            <>
              <div className="chip" style={{ marginBottom: 12 }}>已回答 {qaCount} 题 · 访谈中</div>
              <div style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.6, marginBottom: 14 }}>{question}</div>
              <textarea className="textarea" rows={5} placeholder="把你的真实经验讲出来…" value={answer} disabled={busy} onChange={(e) => setAnswer(e.target.value)} />
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button className="btn btn-primary" disabled={busy || !answer.trim()} onClick={submitAnswer}><Send size={16} /> 提交并继续</button>
                {qaCount >= 1 && <button className="btn" disabled={busy} onClick={synth}><Wand2 size={15} /> 够了，直接合成</button>}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
