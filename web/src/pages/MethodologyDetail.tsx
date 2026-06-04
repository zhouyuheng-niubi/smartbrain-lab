import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Pencil, Play, Share2, Copy, GitFork, ScanSearch, MessagesSquare, Link2, ListChecks, BookText } from 'lucide-react'
import { api } from '../services/api'
import type { Methodology } from '../types'
import { useUI } from '../store'
import SevenSlotEditor from '../components/SevenSlotEditor'
import ChecklistView from '../components/ChecklistView'

export default function MethodologyDetail() {
  const { id = '' } = useParams()
  const nav = useNavigate()
  const notify = useUI((s) => s.notify)
  const [m, setM] = useState<Methodology | null>(null)
  const [raw, setRaw] = useState('')
  const [exported, setExported] = useState<string | null>(null)
  const [view, setView] = useState<'detail' | 'checklist'>('detail')

  useEffect(() => { api.getMethodology(id).then(setM).catch((e) => notify(String(e), 'error')) }, [id])

  if (!m) return <div className="muted">加载中…</div>

  const start = async () => {
    if (!raw.trim()) return notify('先输入要拆解的需求', 'error')
    try {
      const d = await api.createRun({ methodology_id: m.id, raw_input: raw, title: raw.slice(0, 40) })
      nav(`/run/${d.run.id}`)
    } catch (e) { notify(String(e), 'error') }
  }
  const doExport = async () => {
    try { setExported((await api.exportMethodology(m.id)).content) } catch (e) { notify(String(e), 'error') }
  }
  const bindPM = async () => {
    try { await api.setBinding('product_manager', m.id); notify('已绑定到 OPC 产品经理，数字员工将按它行事', 'good') }
    catch (e) { notify(String(e), 'error') }
  }
  const doFork = async () => {
    try {
      const f = await api.forkMethodology(m.id)
      notify('已 fork 成我们公司版（草稿）', 'good')
      nav(`/methodology/${f.id}/edit`)
    } catch (e) { notify(String(e), 'error') }
  }

  const provLabel = (() => {
    const st = m.provenance?.source_type
    if (st === 'builtin') return `大厂出品 · ${m.provenance?.origin || ''}`
    if (st === 'distilled') return `内部蒸馏 · ${m.provenance?.origin || ''}`
    if (m.provenance?.forked_from) return `本地化 · fork 自 ${m.provenance.forked_from}`
    return '本地'
  })()

  return (
    <div style={{ maxWidth: 880, margin: '0 auto' }}>
      <button className="btn" onClick={() => nav('/')} style={{ marginBottom: 16 }}><ArrowLeft size={16} /> 返回</button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 8 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800 }}>{m.name}</h1>
          <p className="muted" style={{ marginTop: 4 }}>{m.summary}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn" onClick={doFork}><GitFork size={15} /> fork 成我们公司版</button>
          <button className="btn" onClick={() => nav(`/methodology/${m.id}/edit`)}><Pencil size={15} /> 编辑</button>
          <button className="btn" onClick={doExport}><Share2 size={15} /> 导出为 Agent 上下文</button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <span className="chip" style={{ borderColor: 'var(--primary)', color: 'var(--primary)' }}>{provLabel}</span>
        {m.status === 'draft' && <span className="chip" style={{ borderColor: 'var(--warn)', color: 'var(--warn)' }}>草稿</span>}
        <span className="chip">{m.origin === 'builtin' ? '内置' : '自定义'}</span>
        <span className="chip">v{m.version}</span>
        <span className="chip">{m.run_count} 次试跑</span>
        {m.avg_artifact_score != null && <span className="chip">均分 {m.avg_artifact_score}</span>}
        {m.tags?.map((t) => <span key={t} className="chip">{t}</span>)}
      </div>

      {/* 用它来…（透镜 / 顾问 / 注入 OPC） */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
        <button className="btn" onClick={() => nav(`/lens?methodology=${m.id}`)}><ScanSearch size={15} /> 用它诊断一份材料</button>
        <button className="btn" onClick={() => nav(`/advisor?methodology=${m.id}`)}><MessagesSquare size={15} /> 找它当顾问</button>
        <button className="btn" onClick={bindPM}><Link2 size={15} /> 绑定到 OPC 产品经理</button>
      </div>

      {/* 试跑 */}
      <div className="card" style={{ padding: 16, marginBottom: 20 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>用这套方法论试跑一个真实需求</div>
        <textarea className="textarea" rows={2} placeholder="例如：给销售做个能看业绩的东西" value={raw} onChange={(e) => setRaw(e.target.value)} />
        <button className="btn btn-primary" style={{ marginTop: 10 }} onClick={start}><Play size={16} /> 开始试跑</button>
      </div>

      {exported && (
        <div className="card" style={{ padding: 16, marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ fontWeight: 700 }}>Agent 可注入上下文（OPC 接缝）</div>
            <button className="btn" onClick={() => { navigator.clipboard?.writeText(exported); notify('已复制', 'good') }}><Copy size={14} /> 复制</button>
          </div>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, lineHeight: 1.6, color: 'var(--muted)' }}>{exported}</pre>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button className="btn" onClick={() => setView('detail')} style={{ borderColor: view === 'detail' ? 'var(--primary)' : 'var(--border)' }}><BookText size={15} /> 七槽位详情</button>
        <button className="btn" onClick={() => setView('checklist')} style={{ borderColor: view === 'checklist' ? 'var(--primary)' : 'var(--border)' }}><ListChecks size={15} /> 检查清单</button>
      </div>
      {view === 'detail' ? <SevenSlotEditor value={m} /> : <ChecklistView gates={m.gates} antiPatterns={m.anti_patterns} />}
    </div>
  )
}
