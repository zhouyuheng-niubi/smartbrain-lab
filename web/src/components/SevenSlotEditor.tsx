import { Plus, Trash2 } from 'lucide-react'
import type { Methodology } from '../types'

type Slots = Pick<Methodology,
  'trigger' | 'principles' | 'steps' | 'gates' | 'anti_patterns' | 'artifacts' | 'metrics'
  | 'applicability' | 'examples' | 'related'>

const LIST_SLOTS: { key: keyof Slots; label: string; hint: string; fields: [string, string, boolean][] }[] = [
  { key: 'principles', label: '信条 / 意识形态', hint: '背后的世界观——为什么这么看问题', fields: [['title', '信条', false], ['detail', '为什么', true]] },
  { key: 'steps', label: '执行步骤', hint: '可一步步走完的有序流程', fields: [['id', 'ID', false], ['name', '名称', false], ['intent', '意图', false], ['guidance', '指引', true]] },
  { key: 'gates', label: '决策闸门', hint: '每步必须回答的硬问题', fields: [['id', 'ID', false], ['step_id', '所属步骤', false], ['question', '问题', true], ['why', '为何重要', false], ['pass_criteria', '通过标准', false]] },
  { key: 'anti_patterns', label: '反模式', hint: '专门警告别犯的错', fields: [['name', '名称', false], ['symptom', '症状', false], ['fix', '纠正', true]] },
  { key: 'artifacts', label: '产出物', hint: '走完后留下什么（合成骨架）', fields: [['name', '名称', false], ['format', '格式', false], ['template', '模板', true]] },
  { key: 'metrics', label: '效果度量', hint: '闭环的钥匙', fields: [['name', '名称', false], ['how_to_measure', '如何度量', false], ['target', '目标', false]] },
  { key: 'examples', label: '案例', hint: '实战正例 / 反例', fields: [['kind', '类型(positive/negative)', false], ['title', '标题', false], ['content', '内容', true]] },
  { key: 'related', label: '关联方法论', hint: '互补 / 冲突 / 上下游', fields: [['slug', '关联 slug', false], ['relation', '关系(complements/conflicts/upstream/downstream)', false], ['note', '说明', false]] },
]

function Section({ title, hint, children }: { title: string; hint: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ padding: 16, marginBottom: 14 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 10 }}>
        <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--primary)' }}>{title}</div>
        <div className="muted" style={{ fontSize: 12 }}>{hint}</div>
      </div>
      {children}
    </div>
  )
}

function DualList({
  label, hint, a, aLabel, b, bLabel, readOnly, onA, onB,
}: {
  label: string; hint: string; a?: string[]; aLabel: string; b?: string[]; bLabel: string
  readOnly: boolean; onA: (v: string[]) => void; onB: (v: string[]) => void
}) {
  const csv = (x?: string[]) => (x || []).join('，')
  const parse = (s: string) => s.split(/[,，]/).map((x) => x.trim()).filter(Boolean)
  return (
    <Section title={label} hint={hint}>
      <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>{aLabel}（逗号分隔）</div>
      {readOnly
        ? <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>{(a || []).map((s, i) => <span key={i} className="chip">{s}</span>)}</div>
        : <input className="input" style={{ marginBottom: 8 }} value={csv(a)} onChange={(e) => onA(parse(e.target.value))} />}
      <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>{bLabel}（逗号分隔）</div>
      {readOnly
        ? <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>{(b || []).map((s, i) => <span key={i} className="chip" style={{ borderColor: 'var(--warn)' }}>{s}</span>)}</div>
        : <input className="input" value={csv(b)} onChange={(e) => onB(parse(e.target.value))} />}
    </Section>
  )
}

export default function SevenSlotEditor({
  value, onChange,
}: { value: Slots; onChange?: (next: Slots) => void }) {
  const readOnly = !onChange
  const patch = (next: Partial<Slots>) => onChange?.({ ...value, ...next })

  const trigger = value.trigger || {}
  const appl = value.applicability || {}

  return (
    <div>
      {/* trigger */}
      <DualList
        label="适用场景 (trigger)" hint="决定方法论何时自动浮现"
        a={trigger.scenarios} aLabel="场景" b={trigger.keywords} bLabel="关键词" readOnly={readOnly}
        onA={(v) => patch({ trigger: { ...trigger, scenarios: v } })}
        onB={(v) => patch({ trigger: { ...trigger, keywords: v } })}
      />

      {/* applicability — 适用/不适用 */}
      <DualList
        label="适用边界 (applicability)" hint="'什么时候别用它'往往比'怎么用'更值钱"
        a={appl.when_to_use} aLabel="✅ 什么时候用" b={appl.when_not_to_use} bLabel="⛔ 什么时候别用" readOnly={readOnly}
        onA={(v) => patch({ applicability: { ...appl, when_to_use: v } })}
        onB={(v) => patch({ applicability: { ...appl, when_not_to_use: v } })}
      />

      {LIST_SLOTS.map(({ key, label, hint, fields }) => {
        const list = (value[key] as Record<string, string>[]) || []
        const update = (i: number, f: string, v: string) => {
          const next = list.map((row, idx) => (idx === i ? { ...row, [f]: v } : row))
          patch({ [key]: next } as Partial<Slots>)
        }
        const add = () => patch({ [key]: [...list, {}] } as Partial<Slots>)
        const remove = (i: number) => patch({ [key]: list.filter((_, idx) => idx !== i) } as Partial<Slots>)
        return (
          <Section key={key} title={`${label} (${key})`} hint={hint}>
            {list.map((row, i) => (
              <div key={i} className="card" style={{ padding: 12, marginBottom: 8, background: 'var(--bg)' }}>
                {fields.map(([f, flabel, long]) => (
                  <div key={f} style={{ marginBottom: 6 }}>
                    <div className="muted" style={{ fontSize: 11, marginBottom: 2 }}>{flabel}</div>
                    {readOnly
                      ? <div style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{row[f] || <span className="muted">—</span>}</div>
                      : long
                        ? <textarea className="textarea" rows={2} value={row[f] || ''} onChange={(e) => update(i, f, e.target.value)} />
                        : <input className="input" value={row[f] || ''} onChange={(e) => update(i, f, e.target.value)} />}
                  </div>
                ))}
                {!readOnly && (
                  <button className="btn" onClick={() => remove(i)} style={{ marginTop: 4 }}><Trash2 size={14} /> 删除</button>
                )}
              </div>
            ))}
            {!readOnly && <button className="btn" onClick={add}><Plus size={14} /> 添加一项</button>}
            {readOnly && list.length === 0 && <div className="muted" style={{ fontSize: 13 }}>—</div>}
          </Section>
        )
      })}
    </div>
  )
}
