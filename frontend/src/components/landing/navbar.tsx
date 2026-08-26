import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BrainCircuit, ArrowRight, Sun, Moon } from 'lucide-react'
import { useAuthStore } from '@/store/auth-store'
import { useUiStore } from '@/store/ui-store'
import { Button } from '@/components/ui'

export function Navbar() {
  const navigate = useNavigate()
  const { token } = useAuthStore()
  const { theme, setTheme } = useUiStore()
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const active = theme === 'dark' || (theme === 'system' && matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', active)
    setDark(active)
  }, [theme])

  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-canvas/85 border-b border-line/80 shadow-soft">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand text-white shadow-soft transition group-hover:scale-105">
            <BrainCircuit className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-xl font-extrabold tracking-tight text-ink dark:text-white leading-none">ClassroomIQ</span>
            <span className="text-[10px] font-semibold text-muted dark:text-slate-300 tracking-wider uppercase mt-0.5">Teaching Intelligence</span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-muted dark:text-slate-200">
          <a href="#features" className="transition hover:text-ink dark:hover:text-white">Capabilities</a>
          <a href="#workflow" className="transition hover:text-ink dark:hover:text-white">Workflow</a>
          <a href="#demo" className="transition hover:text-ink dark:hover:text-white">Live Analysis</a>
          <a href="#pedagogy" className="transition hover:text-ink dark:hover:text-white">Pedagogy</a>
          <a href="#explainability" className="transition hover:text-ink dark:hover:text-white">Explainability</a>
        </nav>

        {/* Auth Actions & Dark/Light Mode Theme Toggle */}
        <div className="flex items-center gap-3">
          {/* Theme Toggle Button */}
          <button
            onClick={() => setTheme(dark ? 'light' : 'dark')}
            aria-label="Toggle dark/light mode theme"
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-surface text-ink dark:text-white hover:bg-canvas transition shadow-soft"
          >
            {dark ? <Sun className="h-5 w-5 text-amber-400" /> : <Moon className="h-5 w-5 text-slate-700" />}
          </button>

          {token ? (
            <Button onClick={() => navigate('/dashboard')} className="gap-2 shadow-soft font-bold">
              <span>Go to Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          ) : (
            <>
              <Link 
                to="/login" 
                className="px-4 py-2 text-sm font-bold text-muted dark:text-slate-200 transition hover:text-ink dark:hover:text-white"
              >
                Sign In
              </Link>
              <Link 
                to="/register" 
                className="inline-flex h-10 items-center justify-center rounded-xl bg-brand px-5 text-sm font-bold text-white shadow-soft transition hover:bg-brand/90 focus-visible:outline-none"
              >
                Get Started Free
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
