import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useUI } from '../../store'

export default function Layout() {
  const { toasts, dismiss } = useUI()
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto', padding: '28px 36px' }}>
        <Outlet />
      </main>

      <div style={{ position: 'fixed', right: 20, bottom: 20, display: 'flex', flexDirection: 'column', gap: 8, zIndex: 50 }}>
        {toasts.map((t) => (
          <div
            key={t.id}
            onClick={() => dismiss(t.id)}
            className="card"
            style={{
              padding: '10px 14px', cursor: 'pointer', maxWidth: 360, fontSize: 13,
              borderColor: t.kind === 'error' ? 'var(--warn)' : t.kind === 'good' ? 'var(--good)' : 'var(--border)',
            }}
          >
            {t.text}
          </div>
        ))}
      </div>
    </div>
  )
}
