import { Link } from 'react-router-dom'
export default function NotFoundPage() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--color-background)', flexDirection: 'column', gap: 16 }}>
      <h1 style={{ fontSize: 72, fontWeight: 800, color: 'var(--color-text-muted)', margin: 0 }}>404</h1>
      <p style={{ fontSize: 18, color: 'var(--color-text-secondary)' }}>Page not found</p>
      <Link to='/dashboard' style={{ color: 'var(--color-brand)', fontWeight: 500, fontSize: 14 }}>Go to Dashboard</Link>
    </div>
  )
}
