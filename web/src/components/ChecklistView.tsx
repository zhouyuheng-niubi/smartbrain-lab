import { useState } from 'react'
import { Square, CheckSquare } from 'lucide-react'
import type { AntiPattern, Gate } from '../types'

/** 嵌入日常：把决策闸门 + 反模式渲染成可勾选的检查清单（决策节点速用，零 LLM）。*/
export default function ChecklistView({ gates, antiPatterns }: { gates: Gate[]; antiPatterns: AntiPattern[] }) {
  const [checked, setChecked] = useState<Record<string, boolean>>({})
  const toggle = (k: string) => setChecked((c) => ({ ...c, [k]: !c[k] }))

  const Item = ({ id, text, sub }: { id: string; text: string; sub?: string }) => (
    <div onClick={() => toggle(id)} style={{ display: 'flex', gap: 10, padding: '8px 0', cursor: 'pointer', alignItems: 'flex-start' }}>
      {checked[id] ? <CheckSquare size={18} color="var(--good)" style={{ flexShrink: 0, marginTop: 2 }} />
        : <Square size={18} color="var(--muted)" style={{ flexShrink: 0, marginTop: 2 }} />}
      <div style={{ opacity: checked[id] ? 0.55 : 1 }}>
        <div style={{ fontSize: 14, textDecoration: checked[id] ? 'line-through' : 'none' }}>{text}</div>
        {sub && <div className="muted" style={{ fontSize: 12 }}>{sub}</div>}
      </div>
    </div>
  )

  const total = gates.length + antiPatterns.length
  const done = Object.values(checked).filter(Boolean).length

  return (
    <div className="card" style={{ padding: 18 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <div style={{ fontWeight: 700 }}>决策检查清单</div>
        <div className="muted" style={{ fontSize: 12 }}>{done}/{total} 已确认</div>
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--primary)', marginTop: 6 }}>每步必答的硬问题</div>
      {gates.map((g) => <Item key={g.id} id={`g-${g.id}`} text={g.question} sub={g.pass_criteria ? `通过标准：${g.pass_criteria}` : undefined} />)}
      {antiPatterns.length > 0 && (
        <>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#f87171', marginTop: 12 }}>确认没踩这些反模式</div>
          {antiPatterns.map((a, i) => <Item key={`a-${i}`} id={`a-${i}`} text={a.name} sub={a.symptom} />)}
        </>
      )}
    </div>
  )
}
