import { Link } from 'react-router-dom'
import { BrainCircuit } from 'lucide-react'

export function Footer() {
  return (
    <footer className="border-t border-line bg-surface py-10 text-xs text-muted">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 sm:flex-row">
        <div className="flex items-center gap-2 font-bold text-ink">
          <div className="grid h-6 w-6 place-items-center rounded-lg bg-brand text-white">
            <BrainCircuit className="h-3.5 w-3.5" />
          </div>
          <span>ClassroomIQ Platform</span>
        </div>

        <div className="flex flex-wrap items-center gap-6">
          <a href="#features" className="hover:text-ink transition">Capabilities</a>
          <a href="#workflow" className="hover:text-ink transition">How It Works</a>
          <a href="#demo" className="hover:text-ink transition">Live Analysis</a>
          <Link to="/login" className="hover:text-ink transition">Sign In</Link>
          <Link to="/register" className="hover:text-ink transition">Register</Link>
        </div>

        <p>© {new Date().getFullYear()} ClassroomIQ Inc. All rights reserved.</p>
      </div>
    </footer>
  )
}
