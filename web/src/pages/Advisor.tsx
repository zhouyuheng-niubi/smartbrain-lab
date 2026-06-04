import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { MessagesSquare, Send } from 'lucide-react'
import { api } from '../services/api'
import type { AdvisorSession, Methodology } from '../types'
import { useUI } from '../store'

export default function Advisor() {
  const { id } = useParams()
  const nav = useNavigate()
  const [sp] = useSearchParams()
  const notify = useUI((s) => s.notify)
  const [methods, setMethods] = useState<Methodology[]>([])
  const [mid, setMid] = useState(sp.get('methodology') || '')
  const [topic, setTopic] = useState('')
  const [session, setSession] = useState<AdvisorSession | null>(null)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (id) {
      api.getAdvisor(id).then((r) => setSession(r.session)).catch((e) => notify(String(e), 'error'))
    } else {
      setSession(null)
      api.listMethodologies().then((d) => {
        setMethods(d.methodologies)
        if (!mid && d.methodologies.length) setMid(d.methodologies[0].id)
      }).catch((e) => notify(String(e), 'error'))
    }
  }, [id])

  const start = async () => {
    if (!mid) return notify('先选一套方法论', 'error')
    setBusy(true)
    try {
      const r = await api.advisorStart({ methodology_id: mid, topic })
      setSession(r.session)
      nav(`/advisor/${r.session.id}`)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  const send = async () => {
    if (!session || !input.trim()) return
    setBusy(true)
    const content = input
    setInput('')
    try {
      const r = await api.advisorMessage(session.id, content)
      setSession(r.session)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  return (
    <div style={{ maxWidth: 820, margin: '0 auto' }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 10 }}>
        <MessagesSquare color="var(--accent)" /> 顾问陪练
      </h1>
      <p className="muted" style={{ marginBottom: 20 }}>
        {session ? `${session.methodology_name} · ${session.topic || '自由讨论'}` : '让一套方法论戴着它的世界观，陪你把一个纠结点想清楚'}
      </p>

      {!session ? (
        <div className="card" style={{ padding: 20 }}>
          <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>请哪套方法论当顾问</div>
          <select className="input" style={{ marginBottom: 12 }} value={mid} onChange={(e) => setMid(e.target.value)}>
            {methods.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>你想讨论的纠结点</div>
          <textarea className="textarea" rows={3} value={topic} onChange={(e) => setTopic(e.target.value)}
            placeholder="例如：要不要自研一套框架，还是用现成的？" />
          <button className="btn btn-primary" style={{ marginTop: 12 }} disabled={busy} onClick={start}>
            <MessagesSquare size={16} /> 开始对话
          </button>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
            {session.messages.map((msg, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div className="card" style={{
                  padding: '10px 14px', maxWidth: '78%', fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap',
                  background: msg.role === 'user' ? 'var(--surface-2)' : 'var(--surface)',
                  borderColor: msg.role === 'assistant' ? 'var(--accent)' : 'var(--border)',
                }}>{msg.content}</div>
              </div>
            ))}
            {busy && <div className="muted" style={{ fontSize: 13 }}>顾问思考中…</div>}
          </div>

          <div className="card" style={{ padding: 12, display: 'flex', gap: 8, alignItems: 'flex-end' }}>
            <textarea className="textarea" rows={2} value={input} disabled={busy}
              onChange={(e) => setInput(e.target.value)} placeholder="说说你的想法…"
              onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send() }} />
            <button className="btn btn-primary" disabled={busy || !input.trim()} onClick={send}><Send size={16} /></button>
          </div>
          <div className="muted" style={{ fontSize: 11, marginTop: 6 }}>⌘/Ctrl + Enter 发送</div>
        </>
      )}
    </div>
  )
}
