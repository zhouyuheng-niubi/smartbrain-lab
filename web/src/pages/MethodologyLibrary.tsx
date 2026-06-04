import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Play, Eye, Plus, Star, Activity } from 'lucide-react'
import { api } from '../services/api'
import type { Methodology, Suggestion } from '../types'
import { useUI } from '../store'
import { BRAND_SUB } from '../brand'

function provBadge(m: Methodology): string {
  const st = m.provenance?.source_type
  if (st === 'builtin') return '大厂出品'
  if (st === 'distilled') return '内部蒸馏'
  if (m.provenance?.forked_from) return '本地化'
  return m.origin === 'builtin' ? '内置' : '自定义'
}

export default function MethodologyLibrary() {
  const nav = useNavigate()
  const notify = useUI((s) => s.notify)
  const [items, setItems] = useState<Methodology[]>([])
  const [q, setQ] = useState('')
  const [origin, setOrigin] = useState<string>('')
  const [raw, setRaw] = useState('')
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [busy, setBusy] = useState(false)

  const load = () =>
    api.listMethodologies({ q: q || undefined, origin: origin || undefined })
      .then((d) => setItems(d.methodologies))
      .catch((e) => notify(String(e), 'error'))

  useEffect(() => { load() }, [q, origin])

  const doSuggest = async () => {
    if (!raw.trim()) return notify('先描述一下你的需求', 'error')
    try {
      const r = await api.suggest(raw)
      setSuggestions(r.suggestions)
      if (!r.suggestions.length) notify('没有匹配的方法论，可直接选下方任意一个试跑')
    } catch (e) { notify(String(e), 'error') }
  }

  const startRun = async (methodology_id: string) => {
    if (!raw.trim()) return notify('先在上方输入要拆解的需求', 'error')
    setBusy(true)
    try {
      const d = await api.createRun({ methodology_id, raw_input: raw, title: raw.slice(0, 40) })
      nav(`/run/${d.run.id}`)
    } catch (e) { notify(String(e), 'error') } finally { setBusy(false) }
  }

  const suggestedIds = useMemo(() => new Set(suggestions.map((s) => s.id)), [suggestions])

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4 }}>方法论库</h1>
      <p className="muted" style={{ marginBottom: 20 }}>{BRAND_SUB}</p>

      {/* 快速试跑 hero */}
      <div className="card" style={{ padding: 20, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, fontWeight: 700 }}>
          <Sparkles size={18} color="var(--primary)" /> 快速试跑：把一句模糊需求丢进来
        </div>
        <textarea
          className="textarea"
          rows={2}
          placeholder="例如：给销售做个能看业绩的东西"
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
        />
        <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <button className="btn" onClick={doSuggest}><Sparkles size={16} /> 推荐方法论</button>
          {suggestions.map((s) => (
            <button key={s.id} className="btn btn-primary" disabled={busy} onClick={() => startRun(s.id)}>
              <Play size={15} /> {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* 过滤 */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <input className="input" style={{ maxWidth: 260 }} placeholder="搜索方法论…" value={q} onChange={(e) => setQ(e.target.value)} />
        {['', 'builtin', 'custom'].map((o) => (
          <button key={o} className="btn" onClick={() => setOrigin(o)}
            style={{ borderColor: origin === o ? 'var(--primary)' : 'var(--border)' }}>
            {o === '' ? '全部' : o === 'builtin' ? '内置' : '自定义'}
          </button>
        ))}
        <button className="btn" style={{ marginLeft: 'auto' }} onClick={() => nav('/new')}><Plus size={16} /> 新建</button>
      </div>

      {/* 卡片网格 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        {items.map((m) => (
          <div key={m.id} className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 10,
            outline: suggestedIds.has(m.id) ? '1.5px solid var(--primary)' : 'none' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{m.name}</div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                {m.status === 'draft' && <span className="chip" style={{ borderColor: 'var(--warn)', color: 'var(--warn)' }}>草稿</span>}
                <span className="chip">{provBadge(m)}</span>
              </div>
            </div>
            <div className="muted" style={{ fontSize: 13, lineHeight: 1.6, minHeight: 40 }}>{m.summary}</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {m.tags?.slice(0, 4).map((t) => <span key={t} className="chip">{t}</span>)}
            </div>
            <div style={{ display: 'flex', gap: 14, fontSize: 12 }} className="muted">
              <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}><Activity size={13} /> {m.run_count} 次试跑</span>
              {m.avg_artifact_score != null &&
                <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}><Star size={13} /> {m.avg_artifact_score} 分</span>}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <button className="btn" onClick={() => nav(`/methodology/${m.id}`)}><Eye size={15} /> 详情</button>
              <button className="btn btn-primary" disabled={busy} onClick={() => startRun(m.id)}><Play size={15} /> 试跑</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
