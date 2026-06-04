import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Star, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react'
import { api } from '../services/api'
import type { Run, RunDetail } from '../types'
import { useUI } from '../store'

const STATUS_LABEL: Record<string, string> = {
  created: '新建', in_progress: '进行中', completed: '已完成', abandoned: '已放弃',
}

export default function RunHistory() {
  const nav = useNavigate()
  const notify = useUI((s) => s.notify)
  const [runs, setRuns] = useState<Run[]>([])
  const [openId, setOpenId] = useState<string | null>(null)
  const [detail, setDetail] = useState<RunDetail | null>(null)
  const [stars, setStars] = useState(0)
  const [adopted, setAdopted] = useState(false)
  const [note, setNote] = useState('')

  useEffect(() => { api.listRuns().then((d) => setRuns(d.runs)).catch((e) => notify(String(e), 'error')) }, [])

  const toggle = async (id: string) => {
    if (openId === id) { setOpenId(null); return }
    setOpenId(id); setStars(0); setAdopted(false); setNote('')
    try { setDetail(await api.getRun(id)) } catch (e) { notify(String(e), 'error') }
  }

  const saveOutcome = async (runId: string) => {
    try {
      await api.recordOutcome(runId, { usefulness: stars, adopted, note })
      notify('已记录效果，闭环完成', 'good')
    } catch (e) { notify(String(e), 'error') }
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 16 }}>试跑历史</h1>
      {runs.length === 0 && <div className="muted">还没有试跑记录。去方法论库开一个吧。</div>}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {runs.map((r) => (
          <div key={r.id} className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: 14, display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }} onClick={() => toggle(r.id)}>
              {openId === r.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{r.title || r.raw_input.slice(0, 40)}</div>
                <div className="muted" style={{ fontSize: 12 }}>{new Date(r.created_at).toLocaleString()}</div>
              </div>
              <span className="chip">{STATUS_LABEL[r.status] || r.status}</span>
              {r.artifact_score && <span className="chip">{r.artifact_score.total} 分</span>}
              <ExternalLink size={15} className="muted" onClick={(e) => { e.stopPropagation(); nav(`/run/${r.id}`) }} />
            </div>

            {openId === r.id && detail?.run.id === r.id && (
              <div style={{ borderTop: '1px solid var(--border)', padding: 16 }}>
                {detail.run.artifact_md
                  ? <div className="markdown"><Markdown remarkPlugins={[remarkGfm]}>{detail.run.artifact_md}</Markdown></div>
                  : <div className="muted" style={{ fontSize: 13 }}>这次试跑还没有产出物（未走完合成）。</div>}

                {/* 效果回填 — 闭环 */}
                <div className="card" style={{ padding: 14, marginTop: 16, background: 'var(--bg)' }}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>记录效果（闭环的钥匙）</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {[1, 2, 3, 4, 5].map((n) => (
                        <Star key={n} size={22} style={{ cursor: 'pointer' }}
                          fill={n <= stars ? 'var(--warn)' : 'none'} color="var(--warn)" onClick={() => setStars(n)} />
                      ))}
                    </div>
                    <label style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 14 }}>
                      <input type="checkbox" checked={adopted} onChange={(e) => setAdopted(e.target.checked)} /> 已采纳
                    </label>
                    <input className="input" style={{ flex: 1, minWidth: 180 }} placeholder="一句话备注…" value={note} onChange={(e) => setNote(e.target.value)} />
                    <button className="btn btn-primary" onClick={() => saveOutcome(r.id)}>记录</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
