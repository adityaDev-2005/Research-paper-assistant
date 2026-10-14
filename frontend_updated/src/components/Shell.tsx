import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Compass, LayoutDashboard, Library, LogOut, Menu, MessageSquareText, NotebookPen, PanelLeftClose, PanelLeftOpen, Search, Settings, User, X } from 'lucide-react'
import { Logo, ThemeToggle } from './ui'
import { useLS } from '../lib/hooks'
import { useAuth, NotImplementedError } from '../auth/auth'

const NAV = [
  { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/app/discover', label: 'Discover Papers', icon: Compass },
  { to: '/app/assistant', label: 'AI Reading Assistant', icon: MessageSquareText },
  { to: '/app/library', label: 'My Library', icon: Library },
  { to: '/app/notes', label: 'Notes & Highlights', icon: NotebookPen },
  { to: '/app/settings', label: 'Settings', icon: Settings },
]
const titleFor = (path: string) => NAV.find((n) => (n.end ? path === n.to : path.startsWith(n.to)))?.label ?? (path.includes('/papers/') ? 'Paper Details' : 'Workspace')

export default function Shell() {
  const [collapsed, setCollapsed] = useLS('ss.sidebar', false)
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState(''); const [menuMsg, setMenuMsg] = useState('')
  const loc = useLocation(); const nav = useNavigate(); const auth = useAuth()
  const menuRef = useRef<HTMLDetailsElement>(null)
  useEffect(() => { setOpen(false) }, [loc.pathname])
  useEffect(() => { const f = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false); addEventListener('keydown', f); return () => removeEventListener('keydown', f) }, [])
  useEffect(() => {
  const handleOutsideClick = (event: PointerEvent) => {
    if (
      menuRef.current &&
      !menuRef.current.contains(event.target as Node)
    ) {
      menuRef.current.open = false
    }
  }

  document.addEventListener('pointerdown', handleOutsideClick)

  return () => {
    document.removeEventListener('pointerdown', handleOutsideClick)
  }
}, [])

  return (
    <div className={`shell ${collapsed ? 'collapsed' : ''}`}>
      <a href="#main" className="skip">Skip to content</a>
      {open && <div className="scrim" onClick={() => setOpen(false)} aria-hidden="true" />}
      <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Workspace navigation">
        <div className="sb-top"><Logo to="/app" />
          <button
            type="button"
            className="icon-btn only-mobile"
            onClick={() => {
              setOpen(false)
              setCollapsed(true)
            }}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>
        <nav>{NAV.map(({ to, label, icon: I, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} title={label}><I size={19} /><span>{label}</span></NavLink>))}</nav>
        <button className="nav-item collapse-btn only-desktop" onClick={() => setCollapsed(!collapsed)} aria-pressed={collapsed} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          {collapsed ? <PanelLeftOpen size={19} /> : <PanelLeftClose size={19} />}<span>Collapse</span></button>
      </aside>
      <div className="main-col">
        <header className="topbar">
          <button className="icon-btn only-mobile" onClick={() => setOpen(true)} aria-label="Open menu"><Menu size={20} /></button>
          <div className="crumb"><span className="muted sm only-desktop">ScholarSpace /</span> <strong>{titleFor(loc.pathname)}</strong></div>
          <form className="topsearch" role="search" onSubmit={(e) => { e.preventDefault(); nav(`/app/discover?q=${encodeURIComponent(q)}`) }}>
            <Search size={16} aria-hidden="true" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search papers" aria-label="Search papers" /></form>
          <ThemeToggle />
          <details className="menu" ref={menuRef}>
            <summary className="icon-btn" aria-label="Profile menu"><User size={18} /></summary>
            <div className="menu-pop">

            <div className="menu-id">
              <strong>{auth.user?.name || 'Guest'}</strong>
              <span
              className="muted sm"
              style={{
                display: 'block',
                maxWidth: '180px',
                overflowWrap: 'anywhere',
                lineHeight: 1.4,
              }}
            >
              {auth.user?.email || 'Not signed in'}
            </span>
            </div>

              <button onClick={() => nav('/app/settings')}><Settings size={15} /> Settings</button>

              <button
                onClick={async () => {
                  setMenuMsg('')
                  try {
                    await auth.signOut()
                    nav('/', { replace: true })
                  } catch (e) {
                    setMenuMsg(
                      e instanceof Error ? e.message : 'Sign-out failed.',
                    )
                  }
                }}
              >
                <LogOut size={15} /> Sign out
              </button>

              {menuMsg && <p className="muted sm menu-msg" role="status">{menuMsg}</p>}
            </div>
          </details>
        </header>
        <main id="main" className="content" tabIndex={-1}><Outlet /></main>
      </div>
    </div>
  )
}
