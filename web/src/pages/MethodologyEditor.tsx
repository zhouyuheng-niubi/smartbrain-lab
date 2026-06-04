import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Save } from 'lucide-react'
import { api } from '../services/api'
import type { Methodology } from '../types'
import { useUI } from '../store'
import SevenSlotEditor from '../components/SevenSlotEditor'

type Draft = Pick<Methodology,
  'name' | 'summary' | 'tags' | 'trigger' | 'principles' | 'steps' | 'gates' | 'anti_patterns'
  | 'artifacts' | 'metrics' | 'applicability' | 'examples' | 'related'>

const EMPTY: Draft = {
  name: '', summary: '', tags: [],
  trigger: { scenarios: [], keywords: [] },
  principles: [], steps: [], gates: [], anti_patterns: [], artifacts: [], metrics: [],
  applicability: { when_to_use: [], when_not_to_use: [] }, examples: [], related: [],
}

export default function MethodologyEditor() {
  const { id } = useParams()
  const nav = useNavigate()
  const notify = useUI((s) => s.notify)
  const [draft, setDraft] = useState<Draft>(EMPTY)
  const [busy, setBusy] = useState(false)
  const editing = Boolean(id)

  useEffect(() => {
    if (!id) return
    api.getMethodology(id).then((m) => setDraft({
      name: m.name, summary: m.summary, tags: m.tags,
      trigger: m.trigger, principles: m.principles, steps: m.steps,
      gates: m.gates, anti_patterns: m.anti_patterns, artifacts: m.artifacts, metrics: m.metrics,
      applicability: m.applicability || {}, examples: m.examples || [], related: m.related || [],
    })).catch((e) => notify(String(e), 'error'))
  }, [id])

  const save = async () => {
    if (!draft.name.trim()) return notify('请填写方法论名称', 'error')
    setBusy(true)
    try {
      if (editing && id) {
        await api.updateMethodology(id, draft)
        notify('已保存（生成新版本）', 'good')
        nav(`/methodology/${id}`)
      } else {
        const m = await api.createMethodology(draft)
        notify('已创建', 'good')
        nav(`/methodology/${m.id}`)
      }
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  return (
    <div style={{ maxWidth: 880, margin: '0 auto' }}>
      <button className="btn" onClick={() => nav(-1)} style={{ marginBottom: 16 }}><ArrowLeft size={16} /> 返回</button>
      <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 16 }}>{editing ? '编辑方法论' : '创作新方法论'}</h1>

      <div className="card" style={{ padding: 16, marginBottom: 14 }}>
        <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>名称</div>
        <input className="input" style={{ marginBottom: 10 }} value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
        <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>一句话简介</div>
        <input className="input" style={{ marginBottom: 10 }} value={draft.summary} onChange={(e) => setDraft({ ...draft, summary: e.target.value })} />
        <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>标签（逗号分隔）</div>
        <input className="input" value={(draft.tags || []).join('，')}
          onChange={(e) => setDraft({ ...draft, tags: e.target.value.split(/[,，]/).map((x) => x.trim()).filter(Boolean) })} />
      </div>

      <SevenSlotEditor value={draft} onChange={(next) => setDraft({ ...draft, ...next })} />

      <button className="btn btn-primary" disabled={busy} onClick={save} style={{ marginTop: 8 }}>
        <Save size={16} /> {editing ? '保存新版本' : '创建方法论'}
      </button>
    </div>
  )
}
