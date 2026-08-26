import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ShieldCheck, 
  BookOpenCheck, 
  GraduationCap, 
  Lightbulb, 
  FileText, 
  Mic, 
  BookOpen, 
  Database, 
  ArrowRight, 
  ArrowDown, 
  CheckCircle2, 
  Sparkles,
  Layers,
  Cpu
} from 'lucide-react'

export function FiveEnginesPipeline() {
  const [activeEngine, setActiveEngine] = useState<number>(1)

  const engines = [
    {
      id: 1,
      num: '01',
      title: 'Technical Claim Validation',
      statusTag: 'Stage 01 Active',
      shortDesc: 'Checks whether technical statements made during the lecture are accurate against authoritative reference materials.',
      icon: ShieldCheck,
      color: 'teal',
      inputSample: '"LL(1) parsers build the parse tree top-down with one lookahead token."',
      processSample: 'Claim extraction ➔ Reference matching ➔ Technical verification',
      outputSample: 'Verified Technical Claim (Status: Verified Factual)',
      evidenceSample: 'Compilers Textbook: Sec 4.4, p. 218',
      whySample: 'Detects technical misconceptions before they affect student understanding.'
    },
    {
      id: 2,
      num: '02',
      title: 'Syllabus Topic Coverage',
      statusTag: 'Stage 02 Active',
      shortDesc: 'Determines what parts of the official syllabus were actually covered and tracks time allocation pacing.',
      icon: BookOpenCheck,
      color: 'blue',
      inputSample: 'Delivered lecture transcript + official course syllabus',
      processSample: 'Map transcript content ➔ Identify syllabus topics ➔ Measure duration',
      outputSample: 'Covered topics & Unit 2 topic coverage alignment',
      evidenceSample: 'Unit 2: Syntax Analysis timestamped excerpt log',
      whySample: 'Shows whether the lecture actually addressed the intended course material.'
    },
    {
      id: 3,
      num: '03',
      title: 'Pedagogical Intelligence',
      statusTag: 'Analysis Connected',
      shortDesc: 'Analyzes how the lecture was taught across 5 pedagogical dimensions such as clarity, examples, pacing & Q&A.',
      icon: GraduationCap,
      color: 'indigo',
      inputSample: 'Lecture transcript and speech delivery patterns',
      processSample: 'Analyze clarity ➔ Count code examples ➔ Measure Q&A ➔ Evaluate flow',
      outputSample: 'Multi-dimensional pedagogical delivery insights',
      evidenceSample: '6 spoken code examples at min 14:20 & 1:4 Q&A ratio',
      whySample: 'Helps faculty understand teaching quality beyond simple attendance or analytics.'
    },
    {
      id: 4,
      num: '04',
      title: 'Actionable Faculty Growth',
      statusTag: 'Action Identified',
      shortDesc: 'Turns detected teaching patterns into prioritized, practical improvement suggestions.',
      icon: Lightbulb,
      color: 'amber',
      inputSample: 'Findings from validation, coverage, and pedagogy engines',
      processSample: 'Identify teaching gaps ➔ Prioritize ➔ Generate evidence-backed actions',
      outputSample: 'Prioritized (HIGH/MEDIUM/LOW) recommendations for faculty',
      evidenceSample: 'Interaction prompt gap logged at timestamp 24:15',
      whySample: 'The system should not merely report problems. It should help improve teaching.'
    },
    {
      id: 5,
      num: '05',
      title: 'Explainable Intelligence',
      statusTag: 'Evidence Linked',
      shortDesc: 'Explains why ClassroomIQ reached its conclusions with transparent reasoning and page-level citations.',
      icon: FileText,
      color: 'purple',
      inputSample: 'All previous engine findings & recommendation verdicts',
      processSample: 'Connect conclusions ➔ Transcript evidence ➔ Reference evidence ➔ Reasoning chain',
      outputSample: 'Auditable, evidence-backed explanations with confidence DAG',
      evidenceSample: '6-Component confidence breakdown & page-level citation',
      whySample: 'Faculty should be able to understand and verify why the system produced a recommendation.'
    }
  ]

  const current = engines.find((e) => e.id === activeEngine)!

  return (
    <section id="features" className="py-24 lg:py-36 border-t border-line bg-canvas relative overflow-hidden">
      {/* Background Glow */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[650px] w-[950px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-tr from-brand/10 via-indigo-500/5 to-purple-500/10 blur-[150px]" />

      <div className="mx-auto max-w-7xl px-6 relative z-10">
        
        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <span className="text-xs sm:text-sm font-mono font-bold uppercase tracking-wider text-brand">
            CONNECTED INTELLIGENCE PIPELINE
          </span>
          <h2 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-ink dark:text-white leading-tight">
            Five Intelligence Engines. One Teaching Picture.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-muted dark:text-slate-200 leading-relaxed font-bold">
            ClassroomIQ takes a delivered lecture and passes it through five connected intelligence engines — checking what was taught, mapping what was covered, understanding how it was taught, identifying improvements, and explaining every conclusion with evidence.
          </p>
        </div>

        {/* Master Connected Pipeline Container */}
        <div className="rounded-3xl border border-line bg-surface/90 dark:bg-slate-900/90 p-6 sm:p-10 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.1)] backdrop-blur-xl space-y-10">
          
          {/* Top Flow */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-6 text-xs sm:text-sm font-mono font-bold">
            <div className="flex items-center gap-2 text-brand">
              <Mic className="h-4 w-4" />
              <span>Delivered Lecture Input</span>
            </div>

            <div className="hidden md:flex items-center gap-1.5 text-muted dark:text-slate-300">
              <span>Speech</span>
              <ArrowRight className="h-3.5 w-3.5" />
              <span>Grounding</span>
              <ArrowRight className="h-3.5 w-3.5" />
              <span>Analysis</span>
              <ArrowRight className="h-3.5 w-3.5" />
              <span>Evidence</span>
            </div>

            <div className="flex items-center gap-2 text-teal-400">
              <ShieldCheck className="h-4 w-4" />
              <span>Verified Teaching Intelligence Output</span>
            </div>
          </div>

          {/* 5 Connected Engine Stage Cards */}
          <div className="hidden lg:grid grid-cols-5 gap-4 relative">
            
            {/* Animated Connector Line */}
            <div className="absolute top-1/2 left-8 right-8 -translate-y-1/2 h-1 bg-line rounded-full -z-0">
              <motion.div 
                animate={{ width: `${((activeEngine - 1) / 4) * 100}%` }}
                transition={{ duration: 0.4 }}
                className="h-full bg-brand rounded-full shadow-soft"
              />
            </div>

            {engines.map((eng) => {
              const Icon = eng.icon
              const isSelected = activeEngine === eng.id
              return (
                <button
                  key={eng.id}
                  onClick={() => setActiveEngine(eng.id)}
                  className={`group flex flex-col justify-between rounded-2xl border p-5 text-left transition-all duration-300 relative bg-surface ${
                    isSelected
                      ? 'border-brand shadow-float ring-2 ring-brand/30 -translate-y-1'
                      : 'border-line hover:border-brand/40 hover:-translate-y-0.5'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded-md border ${
                        isSelected ? 'bg-brand text-white border-brand' : 'bg-brand-soft text-brand border-brand/20'
                      }`}>
                        {eng.num}
                      </span>
                      <div className={`grid h-9 w-9 place-items-center rounded-xl transition ${
                        isSelected ? 'bg-brand text-white shadow-soft' : 'bg-brand-soft text-brand'
                      }`}>
                        <Icon className="h-4 w-4" />
                      </div>
                    </div>

                    <h3 className="text-lg sm:text-xl font-bold text-ink dark:text-white leading-tight group-hover:text-brand transition">
                      {eng.title}
                    </h3>
                    <p className="mt-2 text-sm sm:text-base text-muted dark:text-slate-300 leading-relaxed line-clamp-3 font-semibold">
                      {eng.shortDesc}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-line/60 flex items-center justify-between text-xs font-bold text-brand">
                    <span>{eng.statusTag}</span>
                    <ArrowRight className={`h-4 w-4 transition-transform ${isSelected ? 'translate-x-1' : 'opacity-40'}`} />
                  </div>
                </button>
              )
            })}
          </div>

          {/* Mobile Vertical Stacked Pipeline */}
          <div className="lg:hidden space-y-3">
            {engines.map((eng) => {
              const Icon = eng.icon
              const isSelected = activeEngine === eng.id
              return (
                <div
                  key={eng.id}
                  onClick={() => setActiveEngine(eng.id)}
                  className={`cursor-pointer rounded-2xl border p-4 transition ${
                    isSelected ? 'border-brand bg-surface shadow-soft' : 'border-line bg-surface/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="grid h-9 w-9 place-items-center rounded-xl bg-brand text-white">
                      <Icon className="h-4.5 w-4.5" />
                    </div>
                    <div>
                      <span className="text-xs font-mono font-bold text-brand uppercase">{eng.num} — {eng.statusTag}</span>
                      <h3 className="font-bold text-base text-ink dark:text-white">{eng.title}</h3>
                    </div>
                  </div>
                  <p className="mt-2 text-xs sm:text-sm text-muted dark:text-slate-200 font-medium leading-relaxed">{eng.shortDesc}</p>
                </div>
              )
            })}
          </div>

          {/* Interactive Dynamic Engine Detail Panel */}
          <div className="rounded-3xl border border-brand/30 bg-gradient-to-b from-canvas via-surface to-canvas p-6 sm:p-10 shadow-float">
            <AnimatePresence mode="wait">
              <motion.div
                key={current.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3 }}
                className="space-y-8"
              >
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
                  <div className="flex items-center gap-3">
                    <div className="grid h-11 w-11 place-items-center rounded-xl bg-brand text-white shadow-soft">
                      <current.icon className="h-5 w-5" />
                    </div>
                    <div>
                      <span className="text-xs font-mono font-bold text-brand uppercase">
                        Engine {current.num} Deep-Dive
                      </span>
                      <h3 className="text-2xl sm:text-3xl font-extrabold text-ink dark:text-white">{current.title}</h3>
                    </div>
                  </div>
                  <span className="text-xs sm:text-sm font-bold text-teal-400 bg-teal-500/10 px-3.5 py-1.5 rounded-full border border-teal-400/20 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4" /> {current.statusTag}
                  </span>
                </div>

                {/* 5-Step Detailed Transformation Flow */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  
                  {/* 1. INPUT */}
                  <div className="rounded-2xl border border-line bg-canvas p-4 sm:p-5 flex flex-col justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase tracking-wider block mb-1">
                        01 INPUT
                      </span>
                      <h4 className="font-bold text-sm text-ink dark:text-white mb-2">What Goes In</h4>
                      <p className="text-xs sm:text-sm text-muted dark:text-slate-200 leading-relaxed font-bold">
                        {current.inputSample}
                      </p>
                    </div>
                  </div>

                  {/* 2. PROCESS */}
                  <div className="rounded-2xl border border-line bg-canvas p-4 sm:p-5 flex flex-col justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block mb-1">
                        02 PROCESS
                      </span>
                      <h4 className="font-bold text-sm text-ink dark:text-white mb-2">What Happens</h4>
                      <p className="text-xs sm:text-sm text-brand font-bold leading-relaxed">
                        {current.processSample}
                      </p>
                    </div>
                  </div>

                  {/* 3. OUTPUT (Teal Replace Emerald) */}
                  <div className="rounded-2xl border border-line bg-canvas p-4 sm:p-5 flex flex-col justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-teal-400 uppercase tracking-wider block mb-1">
                        03 OUTPUT
                      </span>
                      <h4 className="font-bold text-sm text-ink dark:text-white mb-2">What Comes Out</h4>
                      <p className="text-xs sm:text-sm text-teal-400 font-bold leading-relaxed">
                        {current.outputSample}
                      </p>
                    </div>
                  </div>

                  {/* 4. EVIDENCE */}
                  <div className="rounded-2xl border border-line bg-canvas p-4 sm:p-5 flex flex-col justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-purple-400 uppercase tracking-wider block mb-1">
                        04 EVIDENCE
                      </span>
                      <h4 className="font-bold text-sm text-ink dark:text-white mb-2">Auditable Proof</h4>
                      <p className="text-xs sm:text-sm text-purple-300 font-bold leading-relaxed">
                        {current.evidenceSample}
                      </p>
                    </div>
                  </div>

                  {/* 5. WHY IT MATTERS */}
                  <div className="rounded-2xl border border-brand/30 bg-brand-soft/40 p-4 sm:p-5 flex flex-col justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block mb-1">
                        05 WHY IT MATTERS
                      </span>
                      <h4 className="font-bold text-sm text-ink dark:text-white mb-2">Faculty Value</h4>
                      <p className="text-xs sm:text-sm text-ink dark:text-white font-bold leading-relaxed">
                        {current.whySample}
                      </p>
                    </div>
                  </div>

                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Bottom Visual Convergence (Teal Replace Emerald) */}
          <div className="rounded-2xl border border-teal-400/30 bg-teal-500/10 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-teal-400 text-slate-950 shadow-soft font-bold">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <div>
                <h4 className="font-bold text-base sm:text-lg text-ink dark:text-white">Verified Teaching Intelligence Output</h4>
                <p className="text-xs sm:text-sm text-muted dark:text-slate-200 font-semibold">
                  ✓ Verified technical claims · ✓ Syllabus coverage · ✓ Pedagogical insights · ✓ Faculty recommendations · ✓ Evidence citations
                </p>
              </div>
            </div>

            <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-400/20 px-4 py-1.5 text-xs font-bold text-teal-300 shrink-0">
              <span>Pipeline Converged</span>
              <CheckCircle2 className="h-4 w-4" />
            </span>
          </div>

        </div>

      </div>
    </section>
  )
}
