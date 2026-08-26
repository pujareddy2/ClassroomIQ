import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  BookOpen, 
  Database, 
  ShieldCheck, 
  ArrowRight, 
  ArrowDown,
  Sparkles, 
  Cpu, 
  GitFork, 
  FileText, 
  ChevronRight, 
  ChevronLeft, 
  X,
  CheckCircle2,
  GraduationCap,
  Lightbulb
} from 'lucide-react'

export function SystemInputOutput() {
  const [activeModalStage, setActiveModalStage] = useState<number | null>(null)

  const stages = [
    {
      id: 1,
      badge: 'STAGE 01',
      title: 'Classroom Input Ingestion',
      subtitle: 'Audio, Syllabus & Reference Collection',
      desc: 'ClassroomIQ receives delivered classroom audio, official course syllabus topics, and textbook reference PDFs to construct the grounding context.',
      inputLabel: 'Delivered Classroom Speech & Documents',
      processLabel: 'Collect ➔ Segment ➔ Hash ➔ Prepare',
      outputLabel: 'Raw Classroom Input Stream',
      flowchartNodes: [
        { step: '01.A', title: 'Lecture Speech', icon: Mic, desc: 'Classroom audio stream' },
        { step: '01.B', title: 'Course Syllabus', icon: BookOpen, desc: 'Official unit structure' },
        { step: '01.C', title: 'Textbook PDFs', icon: Database, desc: 'Reference materials' },
        { step: '01.D', title: 'Ingestion Node', icon: ShieldCheck, desc: 'Grounded context stream' }
      ]
    },
    {
      id: 2,
      badge: 'STAGE 02',
      title: 'Speech Understanding',
      subtitle: 'Waveform to Transcript Segmentation',
      desc: 'Classroom speech is converted into structured, timestamped transcript segments linked to specific speaker turns.',
      inputLabel: 'Audio Waveform Stream',
      processLabel: 'Clean ➔ Transcribe ➔ Diarize ➔ Segment',
      outputLabel: 'Structured Transcript Passages',
      flowchartNodes: [
        { step: '02.A', title: 'Audio Stream', icon: Mic, desc: '44.1 kHz PCM audio' },
        { step: '02.B', title: 'Noise Cleaning', icon: Cpu, desc: 'Acoustic filtering' },
        { step: '02.C', title: 'Speaker Diarization', icon: FileText, desc: 'Faculty/student split' },
        { step: '02.D', title: 'Timestamped Passages', icon: CheckCircle2, desc: 'Structured transcripts' }
      ]
    },
    {
      id: 3,
      badge: 'STAGE 03',
      title: 'Knowledge Grounding',
      subtitle: 'Cross-Referencing Academic Sources',
      desc: 'Transcript content is connected directly to official course syllabus topics and indexed textbook reference materials.',
      inputLabel: 'Transcript Passages + Course Materials',
      processLabel: 'Match Claims ➔ Link Syllabus ➔ Search Textbooks ➔ Verify Context',
      outputLabel: 'Grounded Academic Knowledge Graph',
      flowchartNodes: [
        { step: '03.A', title: 'Transcript Snippets', icon: FileText, desc: 'Spoken technical claims' },
        { step: '03.B', title: 'Syllabus Mapper', icon: BookOpen, desc: 'Unit topic alignment' },
        { step: '03.C', title: 'Textbook Vector Index', icon: Database, desc: '384-d Cosine RAG' },
        { step: '03.D', title: 'Grounded Knowledge', icon: ShieldCheck, desc: 'Verifiable citations' }
      ]
    },
    {
      id: 4,
      badge: 'STAGE 04',
      title: 'Multi-Engine Analysis',
      subtitle: 'Parallel AI Evaluation Paths',
      desc: 'Multiple intelligence engines simultaneously evaluate technical claims, syllabus coverage pacing, teaching clarity, and prioritized growth items.',
      inputLabel: 'Grounded Academic Knowledge',
      processLabel: 'Claim Validation ➔ Coverage Metric ➔ Pedagogy Score ➔ Recommendations',
      outputLabel: 'Multi-Perspective Intelligence Findings',
      flowchartNodes: [
        { step: '04.A', title: 'Grounded Data', icon: Database, desc: 'Verified context' },
        { step: '04.B', title: 'Validation Engine', icon: ShieldCheck, desc: 'Claim accuracy' },
        { step: '04.C', title: 'Pedagogy Engine', icon: GraduationCap, desc: '5-Dimension delivery' },
        { step: '04.D', title: 'Engine Findings', icon: GitFork, desc: 'Multi-perspective output' }
      ]
    },
    {
      id: 5,
      badge: 'STAGE 05',
      title: 'Evidence & Reasoning',
      subtitle: 'Auditable Proof & Citation Linkage',
      desc: 'Conclusions are connected directly to supporting transcript snippets and exact textbook page citations for transparent verification.',
      inputLabel: 'Multi-Engine Intelligence Findings',
      processLabel: 'Assemble DAG ➔ Attach Evidence ➔ Link Citations ➔ Verify Grounding',
      outputLabel: 'Auditable Evidence-Backed Insights',
      flowchartNodes: [
        { step: '05.A', title: 'Engine Findings', icon: GitFork, desc: 'Multi-engine results' },
        { step: '05.B', title: 'DAG Reasoning', icon: Cpu, desc: '6-Component breakdown' },
        { step: '05.C', title: 'Page Citations', icon: BookOpen, desc: 'Textbook evidence' },
        { step: '05.D', title: 'Evidence Chain', icon: ShieldCheck, desc: 'Auditable proof' }
      ]
    },
    {
      id: 6,
      badge: 'STAGE 06',
      title: 'Verified Teaching Intelligence',
      subtitle: 'Human-Understandable Faculty Guidance',
      desc: 'Faculty receive verified claims, syllabus coverage tracking, pedagogical clarity feedback, and actionable improvement recommendations.',
      inputLabel: 'Auditable Evidence Chain',
      processLabel: 'Format ➔ Prioritize ➔ Deliver Guidance',
      outputLabel: 'Grounded Faculty Analytics Output',
      flowchartNodes: [
        { step: '06.A', title: 'Evidence Chain', icon: ShieldCheck, desc: 'Verifiable conclusions' },
        { step: '06.B', title: 'Claim Verdicts', icon: CheckCircle2, desc: 'Fact-check report' },
        { step: '06.C', title: 'Coverage Metrics', icon: BookOpen, desc: 'Syllabus pacing' },
        { step: '06.D', title: 'Faculty Guidance', icon: Lightbulb, desc: 'Actionable next steps' }
      ]
    }
  ]

  return (
    <section className="py-24 lg:py-36 border-t border-line bg-canvas relative overflow-hidden">
      {/* Soft Ambient Background Glow */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[650px] w-[950px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-tr from-brand/10 via-indigo-500/5 to-purple-500/10 blur-[150px]" />

      <div className="mx-auto max-w-7xl px-6 relative z-10">
        
        {/* Section Intro */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <span className="text-xs sm:text-sm font-mono font-bold uppercase tracking-wider text-brand">
            SYSTEM ARCHITECTURE
          </span>
          <h2 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-ink dark:text-white leading-tight">
            From Classroom Input to Verified Intelligence
          </h2>
          <p className="mt-4 text-base sm:text-xl text-muted dark:text-slate-200 leading-relaxed font-bold">
            See how ClassroomIQ transforms a delivered lecture into grounded, explainable teaching intelligence.
          </p>
        </div>

        {/* Master Floating Outer Box */}
        <div className="rounded-3xl border border-line/80 bg-surface/90 dark:bg-slate-900/90 p-8 sm:p-12 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.1)] backdrop-blur-xl relative overflow-hidden">
          
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
            
            {/* LEFT — INPUT */}
            <div className="lg:col-span-3 flex flex-col justify-between space-y-4">
              <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block mb-1">
                INPUT MATERIALS
              </span>

              {/* Input Card 1: Audio */}
              <div 
                onClick={() => setActiveModalStage(1)}
                className="group cursor-pointer rounded-2xl border border-line bg-canvas p-5 transition hover:border-brand hover:shadow-soft flex-1 flex flex-col justify-center"
              >
                <div className="flex items-center gap-3.5">
                  <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand/10 text-brand group-hover:bg-brand group-hover:text-white transition">
                    <Mic className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-base text-ink dark:text-white group-hover:text-brand transition">🎙 Lecture Audio</h4>
                    <p className="text-xs sm:text-sm text-muted dark:text-slate-300 font-semibold mt-0.5">Delivered speech & audio</p>
                  </div>
                </div>
              </div>

              {/* Input Card 2: Syllabus */}
              <div 
                onClick={() => setActiveModalStage(3)}
                className="group cursor-pointer rounded-2xl border border-line bg-canvas p-5 transition hover:border-indigo-500 hover:shadow-soft flex-1 flex flex-col justify-center"
              >
                <div className="flex items-center gap-3.5">
                  <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-indigo-500/10 text-indigo-500 group-hover:bg-indigo-500 group-hover:text-white transition">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-base text-ink dark:text-white group-hover:text-indigo-500 transition">📘 Course Syllabus</h4>
                    <p className="text-xs sm:text-sm text-muted dark:text-slate-300 font-semibold mt-0.5">Official syllabus units</p>
                  </div>
                </div>
              </div>

              {/* Input Card 3: References */}
              <div 
                onClick={() => setActiveModalStage(3)}
                className="group cursor-pointer rounded-2xl border border-line bg-canvas p-5 transition hover:border-purple-500 hover:shadow-soft flex-1 flex flex-col justify-center"
              >
                <div className="flex items-center gap-3.5">
                  <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-purple-500/10 text-purple-500 group-hover:bg-purple-500 group-hover:text-white transition">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-base text-ink dark:text-white group-hover:text-purple-500 transition">📚 Reference Materials</h4>
                    <p className="text-xs sm:text-sm text-muted dark:text-slate-300 font-semibold mt-0.5">Authoritative textbook PDFs</p>
                  </div>
                </div>
              </div>
            </div>

            {/* CENTER — CLASSROOMIQ INTELLIGENCE CORE */}
            <div className="lg:col-span-6 rounded-3xl border border-brand/40 bg-gradient-to-b from-canvas via-surface to-canvas p-6 sm:p-8 shadow-2xl shadow-brand/10 text-center flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-brand via-indigo-500 to-purple-500" />
              
              <div>
                <div className="inline-flex items-center gap-2 rounded-full bg-brand-soft px-4 py-1.5 text-xs font-mono font-bold text-brand mb-4 border border-brand/20">
                  <Cpu className="h-4 w-4 text-brand" />
                  <span>INTELLIGENCE CORE</span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-extrabold text-ink dark:text-white">ClassroomIQ Processing Center</h3>
                <p className="mt-3 text-sm sm:text-base text-muted dark:text-slate-200 max-w-md mx-auto leading-relaxed font-bold">
                  Connects spoken lecture speech against official syllabus units and indexed textbook references.
                </p>

                {/* 4 Discoverable Stages Bar */}
                <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { id: 2, label: 'Understand', icon: FileText },
                    { id: 3, label: 'Ground', icon: Database },
                    { id: 4, label: 'Analyze', icon: GitFork },
                    { id: 5, label: 'Explain', icon: ShieldCheck }
                  ].map((st) => {
                    const StIcon = st.icon
                    return (
                      <button
                        key={st.id}
                        onClick={() => setActiveModalStage(st.id)}
                        className="group flex flex-col items-center justify-center p-4 rounded-2xl border border-line bg-surface hover:border-brand hover:bg-brand-soft/40 transition shadow-soft"
                      >
                        <StIcon className="h-5 w-5 text-brand group-hover:scale-110 transition" />
                        <span className="mt-2 font-bold text-sm sm:text-base text-ink dark:text-white group-hover:text-brand transition">
                          {st.label}
                        </span>
                      </button>
                    )
                  })}
                </div>

                {/* Interactive Exploration Trigger Button */}
                <div className="mt-8">
                  <button
                    onClick={() => setActiveModalStage(2)}
                    className="inline-flex h-12 items-center gap-2.5 rounded-xl bg-brand px-7 text-sm sm:text-base font-bold text-white shadow-float transition hover:bg-brand/90 hover:scale-105 active:scale-95"
                  >
                    <Sparkles className="h-5 w-5" />
                    <span>Explore the Intelligence Pipeline</span>
                    <ArrowRight className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-line text-xs sm:text-sm text-muted dark:text-slate-300 font-bold flex items-center justify-between">
                <span>Zero Arbitrary Telemetry / Verified Process</span>
                <span className="font-bold text-brand">ClassroomIQ Architecture</span>
              </div>
            </div>

            {/* RIGHT — OUTPUT (Teal Accent Replacing Emerald Green) */}
            <div className="lg:col-span-3 flex flex-col justify-between space-y-4">
              <span className="text-xs font-mono font-bold text-teal-400 uppercase tracking-wider block mb-1">
                VERIFIED OUTCOMES
              </span>

              {/* Output Card 1: Verified Claims */}
              <div 
                onClick={() => setActiveModalStage(4)}
                className="group cursor-pointer rounded-2xl border border-line bg-canvas p-5 transition hover:border-teal-400 hover:shadow-soft flex-1 flex flex-col justify-center"
              >
                <div className="flex items-center gap-3.5">
                  <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-teal-500/10 text-teal-400 group-hover:bg-teal-400 group-hover:text-slate-950 transition">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-base text-ink dark:text-white group-hover:text-teal-400 transition">✓ Verified Claims</h4>
                    <p className="text-xs sm:text-sm text-muted dark:text-slate-300 font-semibold mt-0.5">Technical fact-checking</p>
                  </div>
                </div>
              </div>

              {/* Output Card 2: Syllabus Coverage */}
              <div 
                onClick={() => setActiveModalStage(4)}
                className="group cursor-pointer rounded-2xl border border-line bg-canvas p-5 transition hover:border-teal-400 hover:shadow-soft flex-1 flex flex-col justify-center"
              >
                <div className="flex items-center gap-3.5">
                  <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-blue-500/10 text-blue-400 group-hover:bg-blue-400 group-hover:text-slate-950 transition">
                    <BookOpen className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-base text-ink dark:text-white group-hover:text-teal-400 transition">✓ Syllabus Coverage</h4>
                    <p className="text-xs sm:text-sm text-muted dark:text-slate-300 font-semibold mt-0.5">Topic pacing & tracking</p>
                  </div>
                </div>
              </div>

              {/* Output Card 3: Actionable Insights & Evidence */}
              <div 
                onClick={() => setActiveModalStage(5)}
                className="group cursor-pointer rounded-2xl border border-line bg-canvas p-5 transition hover:border-teal-400 hover:shadow-soft flex-1 flex flex-col justify-center"
              >
                <div className="flex items-center gap-3.5">
                  <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-purple-500/10 text-purple-400 group-hover:bg-purple-400 group-hover:text-slate-950 transition">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-base text-ink dark:text-white group-hover:text-teal-400 transition">✓ Explainable Guidance</h4>
                    <p className="text-xs sm:text-sm text-muted dark:text-slate-300 font-semibold mt-0.5">Auditable page citations</p>
                  </div>
                </div>
              </div>
            </div>

          </div>

        </div>

      </div>

      {/* Interactive Discovery Popover Modal */}
      <AnimatePresence>
        {activeModalStage !== null && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ duration: 0.3 }}
              className="relative w-full max-w-3xl rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-10 shadow-2xl text-ink dark:text-white overflow-hidden"
            >
              {/* Modal Top Bar */}
              {(() => {
                const stageInfo = stages.find((s) => s.id === activeModalStage)!
                return (
                  <>
                    <div className="flex items-center justify-between border-b border-line pb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-mono font-bold text-brand bg-brand-soft px-3.5 py-1 rounded-full border border-brand/20">
                          {stageInfo.badge}
                        </span>
                        <h3 className="text-xl sm:text-2xl font-extrabold text-ink dark:text-white leading-none">
                          {stageInfo.title}
                        </h3>
                      </div>

                      <button
                        onClick={() => setActiveModalStage(null)}
                        className="rounded-xl border border-line p-2 text-muted dark:text-slate-200 hover:text-ink dark:hover:text-white hover:bg-canvas transition"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>

                    {/* Modal Body */}
                    <div className="my-6 space-y-6">
                      <div>
                        <p className="text-sm font-bold text-brand">{stageInfo.subtitle}</p>
                        <p className="text-base sm:text-lg text-muted dark:text-slate-200 leading-relaxed font-bold mt-1">{stageInfo.desc}</p>
                      </div>

                      {/* CREATIVE BOXED VISUAL FLOWCHART DIAGRAM */}
                      <div className="rounded-2xl border border-brand/20 bg-canvas p-5 shadow-inner">
                        <span className="text-xs font-mono text-brand font-bold uppercase tracking-wider block mb-3">
                          Pipeline Visual Flowchart Node Diagram:
                        </span>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          {stageInfo.flowchartNodes.map((node, idx) => {
                            const NodeIcon = node.icon
                            return (
                              <div key={idx} className="relative flex flex-col justify-between rounded-xl border border-line bg-surface p-3.5 shadow-soft hover:border-brand/40 transition">
                                <div>
                                  <div className="flex items-center justify-between mb-1.5">
                                    <span className="text-[10px] font-mono text-brand font-bold bg-brand-soft px-2 py-0.5 rounded-md">
                                      {node.step}
                                    </span>
                                    <NodeIcon className="h-4 w-4 text-brand" />
                                  </div>
                                  <h5 className="font-bold text-xs sm:text-sm text-ink dark:text-white leading-tight">{node.title}</h5>
                                </div>
                                <span className="text-[11px] text-muted dark:text-slate-300 font-semibold mt-2 leading-tight block">
                                  {node.desc}
                                </span>
                              </div>
                            )
                          })}
                        </div>
                      </div>

                      {/* Top-to-Bottom Vertical Flowchart Stack */}
                      <div className="space-y-3">
                        <span className="text-xs font-mono text-muted dark:text-slate-300 uppercase tracking-wider block">
                          Stage Transformation Flowchart:
                        </span>

                        {/* Step 1: INPUT */}
                        <div className="rounded-2xl border border-line bg-canvas p-4 flex items-center gap-4 shadow-soft">
                          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand/10 text-brand font-mono font-bold text-xs">
                            IN
                          </div>
                          <div>
                            <span className="text-xs font-mono text-muted dark:text-slate-300 uppercase tracking-wider block">01 — INPUT DATA</span>
                            <span className="font-bold text-sm sm:text-base text-ink dark:text-white">{stageInfo.inputLabel}</span>
                          </div>
                        </div>

                        <div className="flex justify-center -my-1">
                          <ArrowDown className="h-4 w-4 text-brand animate-bounce" />
                        </div>

                        {/* Step 2: PROCESS */}
                        <div className="rounded-2xl border border-brand/30 bg-brand-soft/40 p-4 flex items-center gap-4 shadow-soft">
                          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand text-white font-mono font-bold text-xs">
                            PROC
                          </div>
                          <div>
                            <span className="text-xs font-mono text-brand uppercase tracking-wider block">02 — INTELLIGENCE TRANSFORMATION</span>
                            <span className="font-bold text-sm sm:text-base text-brand">{stageInfo.processLabel}</span>
                          </div>
                        </div>

                        <div className="flex justify-center -my-1">
                          <ArrowDown className="h-4 w-4 text-teal-400" />
                        </div>

                        {/* Step 3: OUTPUT (Teal Replace Green) */}
                        <div className="rounded-2xl border border-teal-400/30 bg-teal-500/10 p-4 flex items-center gap-4 shadow-soft">
                          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-teal-400 text-slate-950 font-mono font-bold text-xs">
                            OUT
                          </div>
                          <div>
                            <span className="text-xs font-mono text-teal-400 uppercase tracking-wider block">03 — VERIFIED INSIGHT</span>
                            <span className="font-bold text-sm sm:text-base text-teal-300">{stageInfo.outputLabel}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Modal Bottom Stepper Controls */}
                    <div className="flex items-center justify-between border-t border-line pt-4">
                      <button
                        disabled={activeModalStage === 1}
                        onClick={() => setActiveModalStage((prev) => (prev ? Math.max(1, prev - 1) : 1))}
                        className="inline-flex h-10 items-center gap-1 rounded-xl border border-line px-4 text-xs sm:text-sm font-bold text-muted dark:text-slate-200 hover:text-ink dark:hover:text-white disabled:opacity-40 transition"
                      >
                        <ChevronLeft className="h-4 w-4" />
                        <span>Previous Stage</span>
                      </button>

                      <div className="flex items-center gap-1.5">
                        {stages.map((st) => (
                          <div
                            key={st.id}
                            className={`h-2.5 rounded-full transition-all ${
                              activeModalStage === st.id ? 'w-7 bg-brand' : 'w-2.5 bg-line'
                            }`}
                          />
                        ))}
                      </div>

                      <button
                        onClick={() => {
                          if (activeModalStage < 6) {
                            setActiveModalStage((prev) => (prev ? prev + 1 : 1))
                          } else {
                            setActiveModalStage(null)
                          }
                        }}
                        className="inline-flex h-10 items-center gap-2 rounded-xl bg-brand px-5 text-xs sm:text-sm font-bold text-white shadow-soft hover:bg-brand/90 transition"
                      >
                        <span>{activeModalStage < 6 ? 'Next Stage' : 'Finish Exploration'}</span>
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </>
                )
              })()}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  )
}
