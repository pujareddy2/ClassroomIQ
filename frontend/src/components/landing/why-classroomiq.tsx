import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, BookOpenCheck, Database, Layers, Lock, Cpu, ArrowDown, Sparkles, CheckCircle2, X } from 'lucide-react'

export function WhyClassroomIQ() {
  const [activeTrustNode, setActiveTrustNode] = useState<number | null>(null)

  const trustLayers = [
    {
      id: 1,
      title: 'Evidence-Backed Analysis',
      subtitle: 'Verified Against Textbook Passages',
      desc: 'Technical findings and claim verdicts are connected directly to supporting reference material passages.',
      icon: ShieldCheck,
      color: 'teal'
    },
    {
      id: 2,
      title: 'Reference Grounding',
      subtitle: 'Academic Reference Matching',
      desc: 'Lecture claims are compared against official course materials and textbook dense vector indices.',
      icon: BookOpenCheck,
      color: 'blue'
    },
    {
      id: 3,
      title: 'Syllabus Awareness',
      subtitle: 'Hierarchical Unit Alignment',
      desc: 'Lecture content is mapped against official syllabus structures to measure actual topic time allocation.',
      icon: Database,
      color: 'indigo'
    },
    {
      id: 4,
      title: 'Explainable Recommendations',
      subtitle: 'Auditable Logical DAG Reasoning',
      desc: 'Faculty recommendations can be traced back to evidence chains and transparent confidence breakdowns.',
      icon: Layers,
      color: 'purple'
    }
  ]

  const sideCapabilities = [
    {
      id: 5,
      title: 'Multi-Course Isolation',
      subtitle: 'Strict Context Separation',
      desc: 'Course data remains completely separated across academic contexts and department boundaries.',
      icon: Lock,
      color: 'amber'
    },
    {
      id: 6,
      title: 'Structured Intelligence',
      subtitle: 'Relational Entity Storage',
      desc: 'Raw lecture speech is transformed into structured, queryable academic relational data entities.',
      icon: Cpu,
      color: 'cyan'
    }
  ]

  const activeCapability = [...trustLayers, ...sideCapabilities].find((c) => c.id === activeTrustNode)

  return (
    <section className="py-24 lg:py-36 border-t border-line bg-canvas relative overflow-hidden">
      {/* Background Glow */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[650px] w-[950px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-tr from-brand/10 via-indigo-500/5 to-purple-500/10 blur-[150px]" />

      <div className="mx-auto max-w-7xl px-6 relative z-10">
        
        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <span className="text-xs sm:text-sm font-mono font-bold uppercase tracking-wider text-brand">
            INSTITUTIONAL TRUST ARCHITECTURE
          </span>
          <h2 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-ink dark:text-white leading-tight">
            Why Institutions Can Trust ClassroomIQ
          </h2>
          <p className="mt-4 text-lg sm:text-xl text-muted dark:text-slate-200 leading-relaxed font-bold">
            ClassroomIQ is built specifically for higher education institutions requiring grounded, auditable academic intelligence and strict multi-course privacy.
          </p>
        </div>

        {/* Master Trust Architecture Layer Diagram */}
        <div className="rounded-3xl border border-line bg-surface/90 dark:bg-slate-900/90 p-8 sm:p-12 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.1)] backdrop-blur-xl space-y-10">
          
          <div className="text-center">
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-soft px-4 py-1.5 text-xs font-mono font-bold text-brand border border-brand/20">
              <Sparkles className="h-4 w-4 text-brand" />
              <span>CLASSROOMIQ TRUST LAYER ARCHITECTURE</span>
            </span>
          </div>

          {/* Central Vertical Stacked Trust Architecture Diagram */}
          <div className="max-w-2xl mx-auto space-y-3">
            {trustLayers.map((layer, idx) => {
              const Icon = layer.icon
              const isSelected = activeTrustNode === layer.id
              return (
                <div key={layer.id} className="space-y-3">
                  <div
                    onClick={() => setActiveTrustNode(layer.id)}
                    className={`cursor-pointer rounded-2xl border p-5 transition-all duration-300 flex items-center justify-between bg-surface ${
                      isSelected
                        ? 'border-brand shadow-float ring-2 ring-brand/30 -translate-y-0.5'
                        : 'border-line hover:border-brand/40'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand text-white shadow-soft font-bold">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <span className="text-xs font-mono font-bold text-brand uppercase block">
                          TRUST LAYER 0{idx + 1}
                        </span>
                        <h4 className="font-bold text-base sm:text-lg text-ink dark:text-white">{layer.title}</h4>
                      </div>
                    </div>

                    <span className="text-xs font-bold text-muted dark:text-slate-300 hidden sm:inline-block">
                      Click for details →
                    </span>
                  </div>

                  {idx < trustLayers.length - 1 && (
                    <div className="flex justify-center -my-1">
                      <ArrowDown className="h-4 w-4 text-brand animate-bounce" />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Surrounding Supporting Capabilities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto pt-6 border-t border-line">
            {sideCapabilities.map((cap) => {
              const Icon = cap.icon
              const isSelected = activeTrustNode === cap.id
              return (
                <div
                  key={cap.id}
                  onClick={() => setActiveTrustNode(cap.id)}
                  className={`cursor-pointer rounded-2xl border p-5 transition-all duration-300 flex items-center gap-4 bg-canvas ${
                    isSelected ? 'border-brand shadow-soft ring-1 ring-brand/20' : 'border-line hover:border-brand/40'
                  }`}
                >
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-soft text-brand">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-xs font-mono font-bold text-brand uppercase block">
                      SECURITY & ARCHITECTURE
                    </span>
                    <h4 className="font-bold text-sm sm:text-base text-ink dark:text-white">{cap.title}</h4>
                  </div>
                </div>
              )
            })}
          </div>

        </div>

      </div>

      {/* Trust Node Interactive Tooltip / Detail Modal */}
      <AnimatePresence>
        {activeTrustNode !== null && activeCapability && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ duration: 0.3 }}
              className="relative w-full max-w-lg rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-8 shadow-2xl text-ink dark:text-white overflow-hidden space-y-4"
            >
              <div className="flex items-center justify-between border-b border-line pb-3">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand text-white">
                    <activeCapability.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-xs font-mono font-bold text-brand uppercase">TRUST ARCHITECTURE</span>
                    <h3 className="text-xl font-extrabold text-ink dark:text-white leading-none">{activeCapability.title}</h3>
                  </div>
                </div>

                <button
                  onClick={() => setActiveTrustNode(null)}
                  className="rounded-xl border border-line p-2 text-muted dark:text-slate-200 hover:text-ink dark:hover:text-white hover:bg-canvas transition"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-bold text-brand">{activeCapability.subtitle}</span>
                <p className="text-base text-muted dark:text-slate-200 font-bold leading-relaxed">
                  {activeCapability.desc}
                </p>
              </div>

              <div className="pt-4 border-t border-line flex justify-end">
                <button
                  onClick={() => setActiveTrustNode(null)}
                  className="inline-flex h-9 items-center rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-soft transition hover:bg-brand/90"
                >
                  <span>Close Detail</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  )
}
