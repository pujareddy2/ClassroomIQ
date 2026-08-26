import { 
  BarChart3, 
  BrainCircuit, 
  HelpCircle, 
  LayoutDashboard, 
  LogOut, 
  Menu, 
  Presentation, 
  Settings, 
  UserRound, 
  X, 
  FolderKanban, 
  LibraryBig,
  Sparkles,
  History
} from 'lucide-react'
import { NavLink, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import { motion } from 'framer-motion'
import { useUiStore } from '@/store/ui-store'
import { useAuthStore } from '@/store/auth-store'

const sections = [
  { 
    label: 'WORKSPACE', 
    items: [
      { to: '/courses', label: 'Courses', icon: FolderKanban },
      { to: '/reference-materials', label: 'Materials', icon: LibraryBig },
      { to: '/lectures', label: 'Lectures', icon: Presentation },
      { to: '/results', label: 'AI Results', icon: Sparkles },
      { to: '/history', label: 'History', icon: History },
      { to: '/analytics', label: 'Insights', icon: BarChart3 },
    ] 
  }
]

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUiStore()
  const { clearSession } = useAuthStore()
  const navigate = useNavigate()

  const logout = () => {
    clearSession()
    navigate('/login')
  }

  return (
    <motion.aside
      animate={{ width: sidebarCollapsed ? 80 : 264 }}
      className="fixed inset-y-0 left-0 z-40 hidden border-r border-line bg-surface p-3 lg:flex lg:flex-col"
    >
      <div className="flex h-14 items-center justify-between px-2">
        <NavLink to="/dashboard" className="flex items-center gap-3 overflow-hidden font-bold">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand text-white shadow-soft">
            <BrainCircuit size={20} />
          </span>
          {!sidebarCollapsed && <span className="text-base font-extrabold text-ink dark:text-white">ClassroomIQ</span>}
        </NavLink>
        <button aria-label="Collapse navigation" onClick={toggleSidebar} className="icon-button hidden xl:inline-flex">
          <Menu size={18} />
        </button>
      </div>

      <NavLink 
        to="/dashboard" 
        className={({ isActive }) => clsx('nav-link mt-4 font-bold', isActive && 'nav-link-active')}
      >
        <LayoutDashboard size={19} />
        <span className={sidebarCollapsed ? 'hidden' : ''}>Dashboard</span>
      </NavLink>

      <nav aria-label="Primary" className="mt-4 space-y-4 overflow-y-auto">
        {sections.map((section) => (
          <section key={section.label}>
            <p className={clsx('px-3 pb-1.5 text-[10px] font-mono font-bold uppercase tracking-widest text-muted dark:text-slate-300', sidebarCollapsed && 'hidden')}>
              {section.label}
            </p>
            {section.items.map(({ to, label, icon: Icon }) => (
              <NavLink 
                key={to} 
                to={to} 
                className={({ isActive }) => clsx('nav-link font-semibold', isActive && 'nav-link-active')}
              >
                <Icon size={19} />
                <span className={sidebarCollapsed ? 'hidden' : ''}>{label}</span>
              </NavLink>
            ))}
          </section>
        ))}
      </nav>

      <div className="mt-auto space-y-1 border-t border-line pt-3">
        <p className={clsx('px-3 pb-1 text-[10px] font-mono font-bold uppercase tracking-widest text-muted dark:text-slate-300', sidebarCollapsed && 'hidden')}>
          ACCOUNT
        </p>
        <NavLink to="/profile" className="nav-link font-semibold">
          <UserRound size={19} />
          <span className={sidebarCollapsed ? 'hidden' : ''}>Profile</span>
        </NavLink>
        <NavLink to="/settings" className="nav-link font-semibold">
          <Settings size={19} />
          <span className={sidebarCollapsed ? 'hidden' : ''}>Settings</span>
        </NavLink>
        <NavLink to="/support" className="nav-link font-semibold">
          <HelpCircle size={19} />
          <span className={sidebarCollapsed ? 'hidden' : ''}>Support</span>
        </NavLink>
        <button onClick={logout} className="nav-link w-full text-danger font-semibold">
          <LogOut size={19} />
          <span className={sidebarCollapsed ? 'hidden' : ''}>Sign Out</span>
        </button>
      </div>
    </motion.aside>
  )
}

export function MobileSidebar({ open, close }: { open: boolean; close: () => void }) {
  return (
    <>
      {open && <button aria-label="Close navigation" onClick={close} className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden backdrop-blur-xs" />}
      <aside className={clsx('fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-line bg-surface p-4 transition-transform lg:hidden', open ? 'translate-x-0' : '-translate-x-full')}>
        <div className="flex items-center justify-between">
          <b className="flex items-center gap-2 font-bold text-ink dark:text-white">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand text-white"><BrainCircuit size={20}/></span>
            ClassroomIQ
          </b>
          <button onClick={close} className="icon-button" aria-label="Close navigation"><X /></button>
        </div>
        <nav className="mt-6 space-y-4">
          <NavLink onClick={close} to="/dashboard" className={({ isActive }) => clsx('nav-link font-bold', isActive && 'nav-link-active')}>
            <LayoutDashboard size={19}/>Dashboard
          </NavLink>
          {sections.map((section) => (
            <section key={section.label}>
              <p className="px-3 pb-1 text-[10px] font-mono font-bold uppercase tracking-widest text-muted dark:text-slate-300">{section.label}</p>
              {section.items.map(({ to, label, icon: Icon }) => (
                <NavLink onClick={close} key={to} to={to} className={({ isActive }) => clsx('nav-link font-semibold', isActive && 'nav-link-active')}>
                  <Icon size={19}/>{label}
                </NavLink>
              ))}
            </section>
          ))}
        </nav>
      </aside>
    </>
  )
}
