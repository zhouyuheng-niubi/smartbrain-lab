import { useEffect, useState } from 'react'
import { Send, HelpCircle } from 'lucide-react'

export default function GateQA({
  question, stepName, busy, onSubmit,
}: {
  question: string
  stepName?: string
  busy: boolean
  onSubmit: (answer: string) => void
}) {
  const [answer, setAnswer] = useState('')
  useEffect(() => { setAnswer('') }, [question])

  return (
    <div className="card" style={{ padding: 20 }}>
      {stepName && <div className="chip" style={{ marginBottom: 12 }}>{stepName}</div>}
      <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
        <HelpCircle size={20} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
        <div style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.6 }}>{question}</div>
      </div>
      <textarea
        className="textarea"
        rows={5}
        placeholder="在这里作答…"
        value={answer}
        disabled={busy}
        onChange={(e) => setAnswer(e.target.value)}
      />
      <button
        className="btn btn-primary"
        style={{ marginTop: 12 }}
        disabled={busy || !answer.trim()}
        onClick={() => onSubmit(answer)}
      >
        <Send size={16} /> {busy ? '判定中…' : '提交作答'}
      </button>
    </div>
  )
}
