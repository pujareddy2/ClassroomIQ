import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  FileText, 
  Database, 
  GitFork, 
  ShieldCheck, 
  Play, 
  Pause, 
  CheckCircle2, 
  BookOpenCheck,
  GraduationCap,
  Lightbulb,
  Layers,
  ArrowRight,
  MessageSquare
} from 'lucide-react'

export function WorkflowPipeline() {
  const [activeStage, setActiveStage] = useState<number>(1)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)

  const stages = [
    {
      id: 1,
      title: 'Lecture Capture',
      badge: 'Stage 01',
      icon: Mic,
      shortDesc: 'Capture the delivered lecture and preserve the context of what was taught.',
      transformTitle: 'Audio Signal Ingestion',
      transformBody: 'Preserves raw spoken classroom audio and speech waveforms from delivered lecture sessions.',
      visualTag: '🎙 Audio Stream Capture'
    },
    {
      id: 2,
      title: 'Speech Understanding',
      badge: 'Stage 02',
      icon: FileText,
      shortDesc: 'Convert classroom speech into structured, analyzable transcript segments.',
      transformTitle: 'Waveform ➔ Text Transformation',
      transformBody: 'Filters filler words and segments speech into timestamped transcript snippets: "LL(1) parsers build parse trees top-down..."',
      visualTag: '⏱ Timestamped Transcript Snippets'
    },
    {
      id: 3,
      title: 'Knowledge Grounding',
      badge: 'Stage 03',
      icon: Database,
      shortDesc: 'Ground the lecture against course curriculum and trusted reference material.',
      transformTitle: 'Academic Reference Matching',
      transformBody: 'Cross-references transcript passages against official syllabus topics and indexed reference textbook passages.',
      visualTag: '📚 Syllabus & Textbook Linkage'
    },
    {
      id: 4,
      title: 'Multi-Engine Analysis',
      badge: 'Stage 04',
      icon: GitFork,
      shortDesc: 'Analyze the lecture across content accuracy, curriculum coverage, teaching quality, interaction, and improvement opportunities.',
      transformTitle: 'Parallel AI Engine Evaluation',
      transformBody: 'Branches lecture data into 5 parallel intelligence evaluation paths.',
      visualTag: '⚡ 5 Intelligence Engines'
    },
    {
      id: 5,
      title: 'Evidence & Explanation',
      badge: 'Stage 05',
      icon: ShieldCheck,
      shortDesc: 'Turn analysis into evidence-backed, explainable teaching insights.',
      transformTitle: 'Grounded Insights & Citations',
      transformBody: 'Converges engine findings into actionable faculty guidance backed by exact transcript evidence and textbook page citations.',
      visualTag: '🎯 Auditable Faculty Report'
    }
  ]

  // Automated step-through pipeline loop
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isPlaying) {
      interval = setInterval(() => {
        setActiveStage((prev) => (prev % 5) + 1)
      }, 3000)
    }
    return () => clearInterval(interval)
  }, [isPlaying])

  const current = stages.find((s) => s.id === activeStage)!

  return (
    <section id="workflow" className="py-20 lg:py-32 border-t border-line bg-canvas relative overflow-hidden">
      {/* Background Soft Glow */}
      <div className="pointer-events-none absolute top-1/3 left-1/2 -z-10 h-[500px] w-[800px] -translate-x-1/2 rounded-full bg-gradient-to-tr from-brand/5 via-indigo-500/5 to-purple-500/5 blur-[120px]" />

      <div className="mx-auto max-w-7xl px-6 relative z-10">
        
        {/* Section Intro Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-line pb-8 mb-12">
          <div>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-brand">
              HOW CLASSROOMIQ WORKS
            </span>
            <h2 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-ink">
              From Lecture to Teaching Intelligence
            </h2>
            <p className="mt-3 text-sm sm:text-base text-muted max-w-2xl leading-relaxed">
              ClassroomIQ transforms delivered classroom speech into grounded, explainable insights — connecting what was taught with what should be taught.
            </p>
          </div>

          {/* Interactive Pipeline Step Control */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className={`inline-flex h-11 items-center gap-2 rounded-xl px-5 text-xs font-bold transition shadow-soft ${
                isPlaying
                  ? 'bg-amber-500 text-slate-950 hover:bg-amber-400'
                  : 'bg-brand text-white hover:bg-brand/90'
              }`}
            >
              {isPlaying ? (
                <>
                  <Pause className="h-4 w-4 fill-current" />
                  <span>Pause Pipeline</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  <span>Explore the Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 5 Primary Interactive Pipeline Stages (Desktop Horizontal Layout) */}
        <div className="hidden lg:grid grid-cols-5 gap-4 relative">
          
          {/* Animated Flow Cable background line */}
          <div className="absolute top-1/2 left-6 right-6 -translate-y-1/2 h-1 bg-line rounded-full -z-0">
            <motion.div 
              animate={{ width: `${((activeStage - 1) / 4) * 100}%` }}
              transition={{ duration: 0.5 }}
              className="h-full bg-brand rounded-full shadow-soft"
            />
          </div>

          {stages.map((st) => {
            const Icon = st.icon
            const isActive = activeStage === st.id
            return (
              <button
                key={st.id}
                onClick={() => {
                  setIsPlaying(false)
                  setActiveStage(st.id)
                }}
                className={`group flex flex-col justify-between rounded-2xl border p-5 text-left transition-all duration-300 relative bg-surface ${
                  isActive
                    ? 'border-brand shadow-float ring-2 ring-brand/20 -translate-y-1'
                    : 'border-line hover:border-brand/40 hover:-translate-y-0.5'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className={`text-[11px] font-mono font-bold ${isActive ? 'text-brand' : 'text-muted'}`}>
                      {st.badge}
                    </span>
                    <div className={`grid h-9 w-9 place-items-center rounded-xl transition ${
                      isActive ? 'bg-brand text-white shadow-soft' : 'bg-brand-soft text-brand'
                    }`}>
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>

                  <h3 className="mt-4 font-bold text-sm text-ink leading-tight group-hover:text-brand transition">
                    {st.title}
                  </h3>
                  <p className="mt-2 text-xs text-muted leading-relaxed line-clamp-2">
                    {st.shortDesc}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-line/60 flex items-center justify-between text-[11px] font-medium text-brand">
                  <span>{st.visualTag}</span>
                  <ArrowRight className={`h-3.5 w-3.5 transition-transform ${isActive ? 'translate-x-1' : ''}`} />
                </div>
              </button>
            )
          })}
        </div>

        {/* Mobile Vertical Connected Pipeline */}
        <div className="lg:hidden space-y-3">
          {stages.map((st) => {
            const Icon = st.icon
            const isActive = activeStage === st.id
            return (
              <div
                key={st.id}
                onClick={() => setActiveStage(st.id)}
                className={`cursor-pointer rounded-2xl border p-4 transition ${
                  isActive ? 'border-brand bg-surface shadow-soft' : 'border-line bg-surface/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-white">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold text-brand uppercase">{st.badge}</span>
                    <h3 className="font-bold text-sm text-ink">{st.title}</h3>
                  </div>
                </div>
                <p className="mt-2 text-xs text-muted leading-relaxed">{st.shortDesc}</p>
              </div>
            )
          })}
        </div>

        {/* Active Stage Data Transformation Inspector */}
        <div className="mt-8 rounded-3xl border border-line bg-surface p-6 sm:p-10 shadow-float relative overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={current.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center"
            >
              {/* Left Column: Stage Explanation */}
              <div className="lg:col-span-6">
                <span className="inline-block rounded-md bg-brand-soft px-3 py-1 text-xs font-bold text-brand mb-2">
                  {current.badge} — {current.visualTag}
                </span>

                <h3 className="text-2xl font-extrabold text-ink">{current.title}</h3>
                <p className="mt-2 text-sm text-muted leading-relaxed">{current.shortDesc}</p>

                <div className="mt-6 rounded-2xl border border-line bg-canvas p-4">
                  <span className="text-[11px] font-mono text-muted uppercase tracking-wider block mb-1">
                    Transformation Process:
                  </span>
                  <h4 className="font-bold text-sm text-ink">{current.transformTitle}</h4>
                  <p className="mt-1 text-xs text-muted leading-relaxed">
                    {current.transformBody}
                  </p>
                </div>
              </div>

              {/* Right Column: Stage Visual Representation */}
              <div className="lg:col-span-6 rounded-2xl border border-line bg-canvas p-6 flex flex-col justify-center min-h-[240px]">
                
                {/* STAGE 01: Lecture Capture */}
                {current.id === 1 && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-line pb-3">
                      <span className="text-xs font-mono text-muted uppercase">Delivered Classroom Audio</span>
                      <span className="text-xs font-semibold text-brand flex items-center gap-1.5">
                        <Mic className="h-4 w-4 animate-pulse" /> Recording Captured
                      </span>
                    </div>
                    <div className="rounded-xl border border-line bg-surface p-4 text-center">
                      <div className="flex justify-center items-center gap-1 h-12">
                        {[40, 70, 30, 90, 50, 80, 40, 100, 60, 40, 80, 50, 90, 30].map((h, idx) => (
                          <div key={idx} className="w-1.5 bg-brand rounded-full transition-all duration-300" style={{ height: `${h}%` }} />
                        ))}
                      </div>
                      <span className="text-[11px] text-muted font-medium mt-2 block">
                        Preserving exact classroom lecture audio & speech context
                      </span>
                    </div>
                  </div>
                )}

                {/* STAGE 02: Speech Understanding */}
                {current.id === 2 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-line pb-3">
                      <span className="text-xs font-mono text-muted uppercase">Structured Transcript Snippets</span>
                      <span className="text-xs font-semibold text-brand">Timestamped Segments</span>
                    </div>
                    <div className="rounded-xl border border-line bg-surface p-3.5 space-y-2 text-xs">
                      <div className="flex items-center justify-between font-mono text-[11px] text-muted">
                        <span>Time 12:40</span>
                        <span>Speaker: Faculty</span>
                      </div>
                      <p className="font-medium text-ink italic">
                        "LL(1) parsers build the parse tree top-down with one lookahead token."
                      </p>
                    </div>
                  </div>
                )}

                {/* STAGE 03: Knowledge Grounding */}
                {current.id === 3 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-line pb-3">
                      <span className="text-xs font-mono text-muted uppercase">Knowledge Grounding Connections</span>
                      <span className="text-xs font-semibold text-emerald-500 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Matched
                      </span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="p-2.5 rounded-xl border border-line bg-surface flex justify-between items-center">
                        <span className="text-muted">Transcript Snippet</span>
                        <span className="font-semibold text-ink">"LL(1) Top-Down Parsing"</span>
                      </div>
                      <div className="p-2.5 rounded-xl border border-line bg-surface flex justify-between items-center">
                        <span className="text-muted">Syllabus Topic</span>
                        <span className="font-semibold text-brand">Unit 2: Syntax Analysis</span>
                      </div>
                      <div className="p-2.5 rounded-xl border border-line bg-surface flex justify-between items-center">
                        <span className="text-muted">Reference Textbook Citation</span>
                        <span className="font-semibold text-emerald-600 dark:text-emerald-400">Compilers Sec 4.4, p. 218</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* STAGE 04: Multi-Engine Analysis (SPECIAL BRANCHING VISUAL) */}
                {current.id === 4 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-line pb-3">
                      <span className="text-xs font-mono text-muted uppercase">Branching Intelligence Graph</span>
                      <span className="text-xs font-semibold text-brand">5 Parallel AI Engines</span>
                    </div>

                    <div className="grid grid-cols-1 gap-2 text-xs">
                      {[
                        { title: 'Technical Validation', desc: 'Checks technical claims against reference materials', icon: ShieldCheck, color: 'text-emerald-500' },
                        { title: 'Syllabus Coverage', desc: 'Measures topic time allocation & pacing', icon: BookOpenCheck, color: 'text-blue-500' },
                        { title: 'Teaching Quality', desc: 'Scores clarity, examples & interaction density', icon: GraduationCap, color: 'text-indigo-500' },
                        { title: 'Student Interaction', desc: 'Tracks Q&A and student engagement ratio', icon: MessageSquare, color: 'text-amber-500' },
                        { title: 'Actionable Recommendations', desc: 'Synthesizes prioritized growth items', icon: Lightbulb, color: 'text-purple-500' }
                      ].map((eng, idx) => {
                        const EngIcon = eng.icon
                        return (
                          <div key={idx} className="flex items-center gap-3 p-2 rounded-xl border border-line bg-surface">
                            <EngIcon className={`h-4 w-4 shrink-0 ${eng.color}`} />
                            <div className="flex justify-between items-center w-full text-[11px]">
                              <span className="font-bold text-ink">{eng.title}</span>
                              <span className="text-muted hidden sm:inline">{eng.desc}</span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* STAGE 05: Evidence & Explanation */}
                {current.id === 5 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-line pb-3">
                      <span className="text-xs font-mono text-muted uppercase">Final Teaching Intelligence</span>
                      <span className="text-xs font-semibold text-emerald-500 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Output Ready
                      </span>
                    </div>

                    <div className="rounded-xl border border-line bg-surface p-4 space-y-2.5 text-xs">
                      <h5 className="font-bold text-ink text-sm">Grounded Academic Intelligence Output</h5>
                      <div className="space-y-1.5 text-muted">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                          <span>Technical claims validated against textbook references</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                          <span>Syllabus topic coverage and time allocation analyzed</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                          <span>Pedagogical clarity & engagement scored across 5 dimensions</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                          <span>Actionable faculty growth recommendations generated</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

              </div>
            </motion.div>
          </AnimatePresence>
        </div>

      </div>
    </section>
  )
}
