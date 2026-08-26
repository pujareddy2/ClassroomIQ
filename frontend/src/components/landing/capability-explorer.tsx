import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, BookOpenCheck, GraduationCap, Lightbulb, FileText, ChevronRight, ArrowRight } from 'lucide-react'

export function CapabilityExplorer() {
  const [selectedEngine, setSelectedEngine] = useState<string>('validation')

  const capabilities = [
    {
      id: 'validation',
      title: 'Technical Claim Validation',
      subtitle: 'Checks technical statements against trusted academic references.',
      metric: '98.4% Confidence',
      icon: ShieldCheck,
      color: 'emerald',
      flow: [
        { step: 'Lecture Claim', val: '"LL(1) parsers build parse tree top-down"' },
        { step: 'Transcript', val: 'Audio Segment #14 (Time 12:40)' },
        { step: 'Reference Match', val: 'Compilers Textbook (Sec 4.4, p. 218)' },
        { step: 'Verification', val: 'Factually Correct & Grounded' }
      ]
    },
    {
      id: 'coverage',
      title: 'Syllabus & Topic Coverage',
      subtitle: 'Maps delivered lecture passages to official curriculum topics.',
      metric: '92% Alignment',
      icon: BookOpenCheck,
      color: 'blue',
      flow: [
        { step: 'Lecture Session', val: 'Session #14 (40 minutes)' },
        { step: 'Topic Detection', val: 'Context-Free Grammars' },
        { step: 'Syllabus Match', val: 'Unit 2: Syntax Analysis' },
        { step: 'Coverage Metric', val: '100% Unit Topic Covered' }
      ]
    },
    {
      id: 'teaching',
      title: 'Pedagogical Intelligence',
      subtitle: 'Evaluates clarity, code example density, Q&A ratio, and pacing.',
      metric: '88/100 Score',
      icon: GraduationCap,
      color: 'indigo',
      flow: [
        { step: 'Lecture Signals', val: 'Speaker Audio & Transcript Rates' },
        { step: '5 Dimensions', val: 'Clarity, Pacing, Examples, Q&A, Flow' },
        { step: 'Analysis Output', val: '6 Code Examples Spoken' },
        { step: 'Pedagogical Score', val: '88 / 100 Overall Performance' }
      ]
    },
    {
      id: 'recommendations',
      title: 'Actionable Faculty Growth',
      subtitle: 'Converts analysis into prioritized, actionable growth suggestions.',
      metric: '3 Priority Actions',
      icon: Lightbulb,
      color: 'amber',
      flow: [
        { step: 'Multi-Engine Input', val: 'Validation + Coverage + Teaching' },
        { step: 'Rule Synthesis', val: 'Detect Pacing & Q&A Gaps' },
        { step: 'Priority Tagging', val: '1 HIGH, 2 MEDIUM Items' },
        { step: 'Action Output', val: 'Increase Student Discussion Time' }
      ]
    },
    {
      id: 'xai',
      title: 'Explainable AI',
      icon: FileText,
      subtitle: 'Provides evidence, reasoning DAGs, and source references.',
      metric: '0.94 Confidence',
      color: 'purple',
      flow: [
        { step: 'AI Verdict', val: 'Claim Verified Factual' },
        { step: 'Reasoning DAG', val: '4 Verified Logical Steps' },
        { step: 'Transcript Snippet', val: 'Timestamped ≤300 char passage' },
        { step: 'Source Reference', val: 'Page-level Textbook Citation' }
      ]
    }
  ]

  const activeCap = capabilities.find(c => c.id === selectedEngine) || capabilities[0]

  return (
    <section id="features" className="py-20 lg:py-28 border-t border-line bg-surface/50">
      <div className="mx-auto max-w-7xl px-6">
        
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-brand">Core Capabilities</span>
          <h2 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-ink">
            From a Lecture to Actionable Intelligence
          </h2>
          <p className="mt-4 text-muted text-sm sm:text-base leading-relaxed">
            ClassroomIQ takes what was actually taught in the classroom and transforms it into structured, evidence-backed insights.
          </p>
        </div>

        {/* 5 Capability Grid */}
        <div className="mt-14 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {capabilities.map((cap) => {
            const Icon = cap.icon
            const isSelected = selectedEngine === cap.id
            return (
              <button
                key={cap.id}
                onClick={() => setSelectedEngine(cap.id)}
                className={`group flex flex-col justify-between rounded-2xl border p-5 text-left transition-all duration-300 ${
                  isSelected
                    ? 'border-brand bg-surface shadow-float ring-2 ring-brand/20'
                    : 'border-line bg-canvas hover:border-brand/40 hover:bg-surface'
                }`}
              >
                <div>
                  <div className={`grid h-10 w-10 place-items-center rounded-xl ${
                    isSelected ? 'bg-brand text-white' : 'bg-brand-soft text-brand'
                  }`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-4 font-bold text-sm text-ink group-hover:text-brand transition">
                    {cap.title}
                  </h3>
                  <p className="mt-1.5 text-xs text-muted leading-relaxed line-clamp-2">
                    "{cap.subtitle}"
                  </p>
                </div>

                <div className="mt-5 flex items-center justify-between border-t border-line/60 pt-3 text-xs font-semibold text-brand">
                  <span>{cap.metric}</span>
                  <ChevronRight className={`h-4 w-4 transition-transform ${isSelected ? 'translate-x-1' : ''}`} />
                </div>
              </button>
            )
          })}
        </div>

        {/* Dynamic Connected Data Visualization Box */}
        <div className="mt-8 rounded-3xl border border-line bg-canvas p-6 sm:p-8 shadow-soft">
          <div className="flex items-center justify-between border-b border-line pb-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-white">
                <activeCap.icon className="h-4 w-4" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-ink">{activeCap.title}</h4>
                <p className="text-xs text-muted">{activeCap.subtitle}</p>
              </div>
            </div>
            <span className="text-xs font-mono font-bold text-brand bg-brand-soft px-3 py-1 rounded-full border border-brand/20">
              {activeCap.metric}
            </span>
          </div>

          {/* Interactive Step Stream */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <AnimatePresence mode="wait">
              {activeCap.flow.map((st, idx) => (
                <motion.div
                  key={`${activeCap.id}-${idx}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.08 }}
                  className="rounded-xl border border-line bg-surface p-4 flex flex-col justify-between"
                >
                  <div>
                    <span className="text-[10px] font-mono uppercase text-muted tracking-wider block">Stage {idx + 1}</span>
                    <span className="font-bold text-xs text-ink block mt-1">{st.step}</span>
                  </div>
                  <div className="mt-3 pt-3 border-t border-line/60">
                    <span className="text-xs font-medium text-brand block">{st.val}</span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

      </div>
    </section>
  )
}
