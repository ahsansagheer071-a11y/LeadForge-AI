import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Search,
  Users,
  Globe,
  Camera,
  Bot,
  MessageSquare,
  Settings,
  LogOut,
  Zap,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { getErrorMessage } from '@/utils'

const NAV_ITEMS = [
  { to: '/dashboard',   icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/discover',    icon: Search,           label: 'Lead Discovery' },
  { to: '/leads',       icon: Users,            label: 'Leads' },
  { to: '/analysis',    icon: Globe,            label: 'Analysis' },
  { to: '/screenshots', icon: Camera,           label: 'Screenshots' },
  { to: '/audit',       icon: Bot,              label: 'AI Audit' },
  { to: '/outreach',    icon: MessageSquare,    label: 'Outreach' },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (e) {
      console.error(getErrorMessage(e))
    }
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.slice(0, 2).toUpperCase() ?? 'LF'

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* ── Sidebar ───────────────────────────────────────── */}
      <aside
        style={{
          width: 232,
          minWidth: 232,
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--color-surface)',
          borderRight: '1px solid var(--color-border)',
          padding: '0 12px',
          overflow: 'hidden',
        }}
      >
        {/* Logo */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '20px 4px 16px',
            borderBottom: '1px solid var(--color-border)',
            marginBottom: 8,
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              background: 'var(--color-brand)',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Zap size={16} color="#fff" strokeWidth={2.5} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: '-0.02em' }}>
            LeadForge AI
          </span>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-item${isActive ? ' active' : ''}`
              }
            >
              <Icon size={16} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Bottom */}
        <div
          style={{
            borderTop: '1px solid var(--color-border)',
            paddingTop: 12,
            paddingBottom: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          <NavLink
            to="/settings"
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <Settings size={16} strokeWidth={1.8} />
            <span>Settings</span>
          </NavLink>

          {/* User row */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 12px',
              borderRadius: 8,
              marginTop: 4,
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: 'var(--color-brand-subtle)',
                border: '1px solid var(--color-brand-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 11,
                fontWeight: 700,
                color: 'var(--color-brand)',
                flexShrink: 0,
              }}
            >
              {initials}
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: 'var(--color-text-primary)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {user?.full_name ?? user?.email?.split('@')[0]}
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--color-text-muted)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {user?.email}
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="btn btn-ghost btn-icon"
              title="Log out"
              style={{ flexShrink: 0 }}
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────── */}
      <main
        style={{
          flex: 1,
          height: '100vh',
          overflowY: 'auto',
          background: 'var(--color-background)',
        }}
      >
        <Outlet />
      </main>
    </div>
  )
}
