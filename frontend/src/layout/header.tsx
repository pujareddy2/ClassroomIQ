import { Bell, Bot, Menu, Moon, Search, Sun, User, Settings, LogOut, ChevronDown } from 'lucide-react'
import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useUiStore } from '@/store/ui-store'
import { useContextStore } from '@/store/context-store'
import { useAssistantStore } from '@/store/assistant-store'
import { useAuthStore } from '@/store/auth-store'

export function Header({ onOpenMobile }: { onOpenMobile: () => void }) {
  const { theme, setTheme, setSearchOpen, setNotificationsOpen, notifications } = useUiStore()
  const setAssistantOpen = useAssistantStore((state) => state.setOpen)
  const { selectedCourseId, selectedCourseName, semester } = useContextStore()
  const { user, clearSession } = useAuthStore()
  const navigate = useNavigate()

  const [dark, setDark] = useState(false)
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const active = theme === 'dark' || (theme === 'system' && matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', active)
    setDark(active)
  }, [theme])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setProfileDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Generate initials avatar (e.g. "Puja Midde" => "PM")
  const getInitials = (name?: string) => {
    if (!name) return 'IQ'
    const parts = name.trim().split(' ')
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    }
    return name.slice(0, 2).toUpperCase()
  }

  const logout = () => {
    clearSession()
    navigate('/login')
  }

  const unread = notifications.filter((n) => !n.read).length

  const courseDisplayName = selectedCourseName || (selectedCourseId ? (selectedCourseId.length > 20 ? 'Active Course' : selectedCourseId) : 'No course selected')

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-line bg-canvas/85 px-4 backdrop-blur lg:px-8">
      {/* Mobile Menu Trigger */}
      <button onClick={onOpenMobile} aria-label="Open navigation" className="icon-button lg:hidden">
        <Menu size={20} />
      </button>

      {/* Global Search Input */}
      <button 
        onClick={() => setSearchOpen(true)} 
        className="hidden h-10 max-w-md flex-1 items-center gap-3 rounded-xl border border-line bg-surface px-3 text-left text-sm text-muted sm:flex"
      >
        <Search size={17} />
        <span className="flex-1">Search anything</span>
        <kbd className="rounded border border-line px-1.5 py-0.5 text-xs">Ctrl K</kbd>
      </button>

      <button onClick={() => setSearchOpen(true)} className="icon-button sm:hidden" aria-label="Search">
        <Search size={19} />
      </button>

      {/* Selected Course Metadata */}
      <div className="ml-auto hidden text-right text-xs text-muted md:block">
        <b className="block text-sm text-ink dark:text-white font-bold">{courseDisplayName}</b>
        <span>{semester ?? 'Semester 6 (2026-2027)'}</span>
      </div>

      {/* AI Assistant Trigger */}
      <button onClick={() => setAssistantOpen(true)} className="icon-button" aria-label="Ask AI assistant">
        <Bot size={19} />
      </button>

      {/* Dark/Light Mode Theme Toggle */}
      <button onClick={() => setTheme(dark ? 'light' : 'dark')} className="icon-button" aria-label="Toggle dark mode">
        {dark ? <Sun size={19} className="text-amber-400" /> : <Moon size={19} />}
      </button>

      {/* Notifications Trigger */}
      <button onClick={() => setNotificationsOpen(true)} className="icon-button relative" aria-label="Open notifications">
        <Bell size={19} />
        {unread > 0 && <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-danger" />}
      </button>

      {/* Top-Right Authenticated User Identity (Avatar + Name Dropdown) */}
      <div className="relative ml-2" ref={dropdownRef}>
        <button
          onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
          className="flex items-center gap-2.5 rounded-xl border border-line bg-surface p-1.5 pr-3 hover:bg-canvas transition shadow-soft"
          aria-label="User profile menu"
        >
          {user?.profileImage ? (
            <img 
              src={user.profileImage} 
              alt={user.full_name} 
              className="h-8 w-8 rounded-lg object-cover border border-line" 
            />
          ) : (
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand via-indigo-500 to-purple-600 text-xs font-extrabold text-white shadow-soft">
              {getInitials(user?.full_name)}
            </div>
          )}

          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs font-bold text-ink dark:text-white leading-none">
              {user?.full_name || 'Faculty Member'}
            </span>
            <span className="text-[10px] text-muted dark:text-slate-300 font-semibold mt-0.5">
              {user?.designation || 'Faculty'}
            </span>
          </div>

          <ChevronDown className="h-3.5 w-3.5 text-muted shrink-0" />
        </button>

        {/* User Identity Dropdown Menu */}
        {profileDropdownOpen && (
          <div className="absolute right-0 mt-2 w-48 rounded-2xl border border-line bg-surface p-2 shadow-float z-50 text-xs space-y-1">
            <div className="px-3 py-2 border-b border-line mb-1">
              <span className="font-bold text-ink dark:text-white block">{user?.full_name}</span>
              <span className="text-[10px] text-muted block truncate">{user?.email}</span>
            </div>

            <Link
              to="/profile"
              onClick={() => setProfileDropdownOpen(false)}
              className="flex items-center gap-2.5 rounded-xl px-3 py-2 font-bold text-ink dark:text-white hover:bg-canvas transition"
            >
              <User className="h-4 w-4 text-brand" />
              <span>Profile</span>
            </Link>

            <Link
              to="/settings"
              onClick={() => setProfileDropdownOpen(false)}
              className="flex items-center gap-2.5 rounded-xl px-3 py-2 font-bold text-ink dark:text-white hover:bg-canvas transition"
            >
              <Settings className="h-4 w-4 text-muted" />
              <span>Settings</span>
            </Link>

            <button
              onClick={logout}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 font-bold text-danger hover:bg-danger/10 transition border-t border-line mt-1 pt-2"
            >
              <LogOut className="h-4 w-4 text-danger" />
              <span>Sign Out</span>
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
