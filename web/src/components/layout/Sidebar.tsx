import { NavLink } from 'react-router-dom'
import { BookOpen, History, PlusCircle, BrainCircuit, FlaskConical, ScanSearch, MessagesSquare } from 'lucide-react'
import { BRAND_NAME, BRAND_TAGLINE } from '../../brand'

const items = [
  { to: '/', icon: BookOpen, label: '方法论库', end: true },
  { to: '/lens', icon: ScanSearch, label: '透镜诊断', end: false },
  { to: '/advisor', icon: MessagesSquare, label: '顾问陪练', end: true },
  { to: '/distill', icon: FlaskConical, label: '蒸馏', end: false },
  { to: '/new', icon: PlusCircle, label: '创作方法论', end: false },
  { to: '/runs', icon: History, label: '试跑历史', end: false },
]

export default function Sidebar() {
  return (
    <aside
      style={{ width: 240, borderRight: '1px solid var(--border)', background: 'rgba(10,16,32,0.6)' }}
      className="h-full flex flex-col p-4 gap-2"
    >
      <div className="flex items-center gap-3 px-2 py-3">
        <div
          style={{ background: 'linear-gradient(160deg, var(--primary), var(--accent))' }}
          className="w-10 h-10 rounded-xl flex items-center justify-center"
        >
          <BrainCircuit size={22} color="#04121f" />
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 16 }}>{BRAND_NAME}</div>
          <div className="muted" style={{ fontSize: 12 }}>{BRAND_TAGLINE}</div>
        </div>
      </div>

      <nav className="flex flex-col gap-1 mt-2">
        {items.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
              borderRadius: 10, fontSize: 14, fontWeight: 600,
              background: isActive ? 'var(--surface-2)' : 'transparent',
              color: isActive ? 'var(--primary)' : 'var(--muted)',
              border: isActive ? '1px solid var(--border)' : '1px solid transparent',
            })}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="muted" style={{ marginTop: 'auto', fontSize: 11, padding: 8, lineHeight: 1.6 }}>
        蒸馏方法论 · 嵌入决策 · 闭环度量
      </div>
    </aside>
  )
}
