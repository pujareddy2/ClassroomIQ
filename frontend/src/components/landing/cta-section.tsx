import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useAuthStore } from '@/store/auth-store'

export function CTASection() {
  const { token } = useAuthStore()

  return (
    <section className="py-24 lg:py-32 border-t border-line bg-surface/80">
      <div className="mx-auto max-w-5xl px-6 text-center">
        <div className="rounded-3xl border border-line bg-gradient-to-b from-canvas via-surface to-canvas p-10 sm:p-16 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.1)] backdrop-blur-xl space-y-8">
          
          {/* Visual Transformation Journey Summary */}
          <div className="inline-flex flex-wrap items-center justify-center gap-2 px-4 py-2 rounded-full border border-brand/20 bg-brand-soft/40 text-xs sm:text-sm font-mono text-brand font-bold shadow-soft">
            <span>LECTURE</span>
            <ArrowRight className="h-3.5 w-3.5" />
            <span>UNDERSTAND</span>
            <ArrowRight className="h-3.5 w-3.5" />
            <span>GROUND</span>
            <ArrowRight className="h-3.5 w-3.5" />
            <span>ANALYZE</span>
            <ArrowRight className="h-3.5 w-3.5" />
            <span>VERIFY</span>
            <ArrowRight className="h-3.5 w-3.5" />
            <span className="text-teal-400">TEACHING INTELLIGENCE</span>
          </div>

          {/* Main Headline */}
          <h2 className="text-3xl font-extrabold tracking-tight sm:text-5xl text-ink dark:text-white leading-tight">
            Turn Every Lecture Into <br />
            <span className="bg-gradient-to-r from-brand via-indigo-500 to-purple-600 bg-clip-text text-transparent">
              Measurable Teaching Intelligence.
            </span>
          </h2>

          {/* Supporting Text */}
          <p className="mx-auto max-w-2xl text-base sm:text-lg text-muted dark:text-slate-200 leading-relaxed font-bold">
            See what was taught. See what was covered. See what needs attention. See why the system reached its conclusion.
          </p>

          {/* CTAs */}
          <div className="pt-4 flex flex-wrap justify-center gap-4">
            <Link
              to={token ? "/dashboard" : "/register"}
              className="inline-flex h-13 items-center justify-center gap-2.5 rounded-xl bg-brand px-8 text-base font-bold text-white shadow-float transition hover:bg-brand/90 hover:scale-105 active:scale-95"
            >
              <span>{token ? "Open Workspace" : "Analyze Your First Lecture"}</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              to={token ? "/dashboard" : "/login"}
              className="inline-flex h-13 items-center justify-center gap-2 rounded-xl border border-line bg-surface px-8 text-base font-bold text-ink dark:text-white shadow-soft transition hover:bg-canvas"
            >
              <span>Sign In</span>
            </Link>
          </div>

        </div>
      </div>
    </section>
  )
}
