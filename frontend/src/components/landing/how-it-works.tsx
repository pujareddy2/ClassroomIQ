import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  FileText, 
  Database, 
  GitFork, 
  ShieldCheck, 
  CheckCircle2, 
  ArrowRight,
  ArrowDown,
  Sparkles,
  BookOpen,
  GraduationCap,
  Lightbulb
} from 'lucide-react'

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState<number>(1)

  const steps = [
    {
      id: 1,
      num: '01',
      action: 'CAPTURE',
      title: 'Delivered Classroom Audio',
      stateTag: 'CAPTURED',
      desc: 'Classroom speech is captured live during the delivered lecture and converted into structured, high-fidelity audio streams.',
      icon: Mic,
      visualBadge: 'LIVE AUDIO WAVEFORM',
      visualSub: 'High-Fidelity Audio Stream Ingestion',
      pipelineNode: 'Live Speech ➔ Noise Filter ➔ Audio Buffer ➔ Stream Ingest'
    },
    {
      id: 2,
      num: '02',
      action: 'UNDERSTAND',
      title: 'Speech & Speaker Segmentation',
      stateTag: 'UNDERSTOOD',
      desc: 'Spoken sentences are converted into timestamped transcript passages linked directly to specific speaker turns.',
      icon: FileText,
      visualBadge: 'SPEECH ➔ TRANSCRIPT',
      visualSub: 'Timestamped Diarized Transcript Passages',
      pipelineNode: 'Audio Passages ➔ Clean Speech ➔ Diarization ➔ Timestamped Sentences'
    },
    {
      id: 3,
      num: '03',
      action: 'GROUND',
      title: 'Course & Textbook Matching',
      stateTag: 'GROUNDED',
      desc: 'Spoken content is connected directly to official course syllabus topics and indexed textbook reference materials.',
      icon: Database,
      visualBadge: 'TRANSCRIPT ➔ KNOWLEDGE GRAPH',
      visualSub: 'Official Syllabus & Textbook PDF Alignment',
      pipelineNode: 'Transcript Snippet ➔ Topic Matching ➔ Course Syllabus ➔ Textbook RAG'
    },
    {
      id: 4,
      num: '04',
      action: 'ANALYZE',
      title: 'Multi-Engine Evaluation',
      stateTag: 'ANALYZED',
      desc: 'Parallel intelligence engines evaluate technical claim accuracy, syllabus coverage pacing, teaching clarity, and prioritized growth items.',
      icon: GitFork,
      visualBadge: 'MULTI-ENGINE ANALYSIS',
      visualSub: 'Parallel Accuracy, Pacing & Pedagogy Evaluation',
      pipelineNode: 'Grounded Data ➔ Claim Check ➔ Coverage Metric ➔ Pedagogy Score'
    },
    {
      id: 5,
      num: '05',
      action: 'EXPLAIN',
      title: 'Evidence-Backed Insights',
      stateTag: 'EXPLAINED',
      desc: 'Conclusions are linked directly to supporting transcript snippets and exact textbook page citations for complete verification.',
      icon: ShieldCheck,
      visualBadge: 'VERIFIED INTELLIGENCE',
      visualSub: 'Auditable Page Citations & Faculty Guidance',
      pipelineNode: 'Engine Findings ➔ Transcript Excerpt ➔ Textbook Page Citation ➔ Faculty Action'
    }
  ]

  const current = steps.find((s) => s.id === activeStep)!

  return (
    <section id="how-it-works" className="py-24 lg:py-36 border-t border-line bg-canvas relative overflow-hidden">
      {/* Background Ambient Glow */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[650px] w-[950px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-tr from-brand/10 via-indigo-500/5 to-purple-500/10 blur-[150px]" />

      <div className="mx-auto max-w-7xl px-6 relative z-10">
        
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <span className="text-xs sm:text-sm font-mono font-bold uppercase tracking-wider text-brand">
            SYSTEM WORKFLOW
          </span>
          <h2 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-ink dark:text-white leading-tight">
            How ClassroomIQ Works
          </h2>
          <p className="mt-4 text-lg sm:text-xl text-muted dark:text-slate-200 leading-relaxed font-bold">
            From the moment a lecture is delivered to the moment a faculty member receives an evidence-backed insight, ClassroomIQ transforms classroom speech into structured academic intelligence.
          </p>
        </div>

        {/* Large 2-Column Split Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-stretch">
          
          {/* LEFT COLUMN: Image Anchor */}
          <div className="lg:col-span-5 flex flex-col justify-between">
            <div className="rounded-3xl overflow-hidden border border-line bg-surface p-3 shadow-[0_20px_50px_rgba(0,0,0,0.08)] relative group flex-1 flex flex-col">
              <div className="relative rounded-2xl overflow-hidden flex-1 min-h-[380px] lg:min-h-[460px]">
                {/* Real Authentic University Classroom Photograph */}
                <img 
                  src="https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1200&q=80" 
                  alt="Real University Classroom Lecture Session" 
                  className="w-full h-full object-cover object-center filter brightness-95"
                />
                
                {/* Gradient Overlays */}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/40 to-transparent pointer-events-none" />

                {/* Top Dynamic Stage Status Indicator */}
                <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-slate-950/80 px-3.5 py-1 text-xs font-mono font-bold text-white backdrop-blur-md shadow-md">
                    <Sparkles className="h-3.5 w-3.5 text-brand" />
                    <span>Stage {current.num} — {current.stateTag}</span>
                  </span>

                  <span className="rounded-full border border-white/20 bg-teal-500/20 px-3 py-1 text-xs font-bold text-teal-300 backdrop-blur-md">
                    System State: {current.stateTag}
                  </span>
                </div>

                {/* Bottom Dynamic Stage Visual Overlay */}
                <div className="absolute bottom-4 left-4 right-4 rounded-2xl border border-white/20 bg-slate-950/85 p-5 backdrop-blur-md text-white shadow-xl space-y-3">
                  <div className="flex items-center justify-between border-b border-white/15 pb-2">
                    <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider">
                      {current.visualBadge}
                    </span>
                    <span className="text-xs text-slate-100 font-bold">{current.action}</span>
                  </div>

                  <p className="text-sm font-bold text-white leading-snug">
                    {current.visualSub}
                  </p>

                  <div className="rounded-xl border border-white/15 bg-white/10 p-3 text-xs font-mono text-slate-100">
                    <span className="text-[10px] text-slate-300 block mb-0.5 font-bold">TRANSFORMATION NODE:</span>
                    <span className="text-brand font-bold block">{current.pipelineNode}</span>
                  </div>
                </div>

              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Connected Vertical Workflow Steps */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-4 relative">
            
            {/* Glowing Vertical Connector Line */}
            <div className="absolute top-8 bottom-8 left-8 w-1 bg-line rounded-full -z-0 hidden sm:block">
              <motion.div 
                animate={{ height: `${((activeStep - 1) / 4) * 100}%` }}
                transition={{ duration: 0.4 }}
                className="w-full bg-brand rounded-full shadow-soft"
              />
            </div>

            {steps.map((st) => {
              const Icon = st.icon
              const isActive = activeStep === st.id
              const isCompleted = activeStep > st.id
              return (
                <div
                  key={st.id}
                  onClick={() => setActiveStep(st.id)}
                  className={`group cursor-pointer rounded-2xl border p-5 transition-all duration-300 relative bg-surface ${
                    isActive
                      ? 'border-brand shadow-float ring-2 ring-brand/20 -translate-y-0.5'
                      : 'border-line hover:border-brand/40 hover:bg-surface/80'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl font-bold transition ${
                        isActive
                          ? 'bg-brand text-white shadow-float'
                          : isCompleted
                          ? 'bg-teal-400 text-slate-950 font-extrabold'
                          : 'bg-brand-soft text-brand'
                      }`}>
                        {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-mono font-bold uppercase tracking-wider ${
                            isActive ? 'text-brand' : 'text-muted dark:text-slate-300'
                          }`}>
                            {st.num} — {st.action}
                          </span>
                          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md ${
                            isActive ? 'bg-brand/10 text-brand' : 'bg-canvas text-muted dark:text-slate-300'
                          }`}>
                            {st.stateTag}
                          </span>
                        </div>

                        <h3 className="text-lg sm:text-xl font-bold text-ink dark:text-white group-hover:text-brand transition mt-0.5">
                          {st.title}
                        </h3>
                      </div>
                    </div>

                    <ArrowRight className={`h-5 w-5 transition-transform ${
                      isActive ? 'text-brand translate-x-1' : 'text-muted opacity-40'
                    }`} />
                  </div>

                  {/* Explanation */}
                  <p className="mt-3 text-base text-muted dark:text-slate-200 font-bold leading-relaxed pl-15">
                    {st.desc}
                  </p>

                  {/* Compact Transformation Node */}
                  {isActive && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      transition={{ duration: 0.3 }}
                      className="mt-4 pt-4 border-t border-line/60 pl-15 space-y-3"
                    >
                      <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">
                        STAGE {st.num} TRANSFORMATION FLOW:
                      </span>

                      <div className="rounded-xl border border-brand/30 bg-canvas p-4 text-xs font-mono">
                        <span className="text-brand font-bold block">{st.pipelineNode}</span>
                      </div>
                    </motion.div>
                  )}
                </div>
              )
            })}

            {/* Stage 05 Final Convergence Banner (Teal Replace Emerald) */}
            {activeStep === 5 && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="rounded-2xl border border-teal-400/40 bg-teal-500/10 p-5 backdrop-blur-md flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-6 w-6 text-teal-400 shrink-0" />
                  <div>
                    <span className="text-xs font-mono font-bold text-teal-300 uppercase block">
                      INTELLIGENCE READY
                    </span>
                    <h4 className="font-bold text-sm sm:text-base text-ink dark:text-white">Evidence-Backed Teaching Intelligence</h4>
                    <p className="text-xs text-muted dark:text-slate-200 font-semibold">
                      ✓ Verified Claims · ✓ Syllabus Coverage · ✓ Pedagogical Insights · ✓ Faculty Recommendations · ✓ Evidence
                    </p>
                  </div>
                </div>
              </motion.div>
            )}

          </div>

        </div>

      </div>
    </section>
  )
}
