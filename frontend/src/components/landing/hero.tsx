import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, CheckCircle2, ShieldCheck, Sparkles, Mic, BookOpen, FileText, ArrowDown } from 'lucide-react'
import { useAuthStore } from '@/store/auth-store'

export function Hero() {
  const { token } = useAuthStore()

  const scrollToWorkflow = (e: React.MouseEvent) => {
    e.preventDefault()
    document.getElementById('workflow')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden py-16 lg:py-24 bg-slate-950">
      {/* High Quality Authentic Real Classroom Photography Background — Bright & Visible */}
      <div className="absolute inset-0 z-0">
        <img 
          src="https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1600&q=80" 
          alt="Real University Classroom & Educator Lecturing" 
          className="h-full w-full object-cover object-center scale-100 filter brightness-95 opacity-65"
        />
        {/* Translucent Side Gradient Overlay — Preserves Photo Visibility Across Entire Canvas */}
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950/80 via-slate-950/60 to-slate-950/30" />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/50 via-transparent to-slate-950" />
      </div>

      {/* Floating Content directly on top of the Background */}
      <div className="relative z-10 mx-auto max-w-7xl px-6 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Clear Value Proposition */}
          <div className="lg:col-span-7 text-left">
            
            {/* Eyebrow Badge */}
            <motion.div 
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-1.5 text-xs sm:text-sm font-bold text-white shadow-lg backdrop-blur-md mb-6"
            >
              <Sparkles className="h-4 w-4 text-brand" />
              <span>Evidence-Backed Teaching Intelligence</span>
            </motion.div>

            {/* Main Headline */}
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-4xl font-extrabold tracking-tight sm:text-6xl sm:leading-[1.12] text-white drop-shadow-md"
            >
              Turn Every Lecture Into <br />
              <span className="bg-gradient-to-r from-brand via-indigo-300 to-purple-300 bg-clip-text text-transparent">
                Teaching Intelligence.
              </span>
            </motion.h1>

            {/* Simplified Wording */}
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mt-6 text-base sm:text-lg text-slate-100 leading-relaxed max-w-xl font-bold drop-shadow-md"
            >
              ClassroomIQ turns delivered lectures into evidence-backed teaching insights by understanding what was taught, comparing it with trusted academic references, and analyzing how it was taught.
            </motion.p>

            {/* CTAs */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mt-8 flex flex-wrap items-center gap-4"
            >
              <Link
                to={token ? "/dashboard" : "/register"}
                className="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-brand px-7 text-base font-bold text-white shadow-float transition hover:bg-brand/90 hover:scale-105 active:scale-95"
              >
                <span>{token ? "Open Workspace" : "Get Started Free"}</span>
                <ArrowRight className="h-5 w-5" />
              </Link>
              <a
                href="#workflow"
                onClick={scrollToWorkflow}
                className="inline-flex h-12 items-center justify-center gap-2 rounded-xl border border-white/30 bg-white/15 px-7 text-base font-bold text-white backdrop-blur-md shadow-lg transition hover:bg-white/25"
              >
                <span>Explore How It Works</span>
              </a>
            </motion.div>

            {/* Trust Row */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="mt-10 flex flex-wrap items-center gap-6 text-xs sm:text-sm text-slate-100 font-bold border-t border-white/20 pt-6"
            >
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-teal-400" /> Evidence grounded
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-teal-400" /> Reference-backed
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-teal-400" /> Explainable insights
              </span>
            </motion.div>
          </div>

          {/* Right Column: High-End Glassmorphic Live Intelligence Transformation Panel */}
          <div className="lg:col-span-5 relative">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, delay: 0.3 }}
              className="rounded-3xl border border-white/25 bg-slate-900/50 p-6 sm:p-8 shadow-[0_0_50px_rgba(0,0,0,0.6)] backdrop-blur-2xl text-white space-y-4"
            >
              <div className="flex items-center justify-between border-b border-white/15 pb-3">
                <span className="text-xs sm:text-sm font-mono font-bold text-brand uppercase tracking-wider">
                  LIVE TRANSFORM FLOW
                </span>
                <span className="text-xs font-bold text-slate-100">ClassroomIQ System</span>
              </div>

              {/* Transformation Step 1 */}
              <div className="rounded-2xl border border-white/20 bg-white/10 p-4 backdrop-blur-md transition hover:bg-white/15 hover:border-white/30 flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-blue-500/30 border border-blue-400/40 text-blue-300">
                    <Mic className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-sm sm:text-base font-bold block text-white">01 — Lecture Audio</span>
                    <span className="text-xs sm:text-sm text-slate-100 font-semibold">Delivered speech & classroom audio</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-center -my-2">
                <ArrowDown className="h-5 w-5 text-brand animate-bounce" />
              </div>

              {/* Transformation Step 2 */}
              <div className="rounded-2xl border border-white/20 bg-white/10 p-4 backdrop-blur-md transition hover:bg-white/15 hover:border-white/30 flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-indigo-500/30 border border-indigo-400/40 text-indigo-300">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-sm sm:text-base font-bold block text-white">02 — Understand & Extract</span>
                    <span className="text-xs sm:text-sm text-slate-100 font-semibold">Technical claims, syllabus topics, delivery</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-center -my-2">
                <ArrowDown className="h-5 w-5 text-brand animate-bounce" />
              </div>

              {/* Transformation Step 3 */}
              <div className="rounded-2xl border border-white/20 bg-white/10 p-4 backdrop-blur-md transition hover:bg-white/15 hover:border-white/30 flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-purple-500/30 border border-purple-400/40 text-purple-300">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-sm sm:text-base font-bold block text-white">03 — Ground Against References</span>
                    <span className="text-xs sm:text-sm text-slate-100 font-semibold">Official syllabus & textbook PDFs</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-center -my-2">
                <ArrowDown className="h-5 w-5 text-teal-400" />
              </div>

              {/* Transformation Step 4: Final Output (Teal Accent Replace Green) */}
              <div className="rounded-2xl border border-teal-400/40 bg-teal-500/20 p-4 backdrop-blur-md flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-teal-500/30 border border-teal-400/50 text-teal-300">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-sm sm:text-base font-bold block text-white">04 — Evidence-Backed Insights</span>
                    <span className="text-xs sm:text-sm text-teal-200 font-bold">Auditable faculty recommendations</span>
                  </div>
                </div>
              </div>

            </motion.div>
          </div>

        </div>
      </div>
    </section>
  )
}
