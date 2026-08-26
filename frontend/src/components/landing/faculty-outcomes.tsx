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
  X,
  ChevronRight,
  Cpu
} from 'lucide-react'

export function FacultyOutcomes() {
  const [selectedOutput, setSelectedOutput] = useState<number | null>(null)

  const outputNodes = [
    {
      id: 1,
      title: 'Technical Accuracy',
      question: 'Which spoken claims require review?',
      statusTag: 'Verified Factual',
      color: 'teal',
      icon: ShieldCheck,
      shortDesc: 'Checks spoken technical statements against textbook references.',
      flowSteps: ['Claim Detected', 'Reference Matched', 'Claim Verified', 'Evidence Attached'],
      demoClaim: 'Spoken Claim: "LL(1) parsers build parse trees top-down with one lookahead token."',
      demoResult: 'Status: Verified Factual · Grounded in Academic Standards',
      demoReference: 'Compilers Textbook: Section 4.4, Page 218',
      demoWhy: 'Detects technical misconceptions before they affect student understanding.'
    },
    {
      id: 2,
      title: 'Syllabus Coverage',
      question: 'Which syllabus topics were covered or missed?',
      statusTag: 'Topic Aligned',
      color: 'blue',
      icon: BookOpenCheck,
      shortDesc: 'Maps lecture topics against official syllabus units and duration.',
      flowSteps: ['Lecture Topic', 'Syllabus Unit Matched', 'Coverage Evaluated', 'Coverage Insight'],
      demoClaim: 'Delivered Content: Unit 2 Syntax Analysis & Predictive Parsing',
      demoResult: 'Status: Unit 2 Topic Aligned · 45 min allocated',
      demoReference: 'Official Course Syllabus: CS301 Unit 2 Learning Objectives',
      demoWhy: 'Shows whether the lecture actually addressed intended course material.'
    },
    {
      id: 3,
      title: 'Pedagogical Quality',
      question: 'How clear and structured was the lecture delivery?',
      statusTag: 'High Density',
      color: 'indigo',
      icon: GraduationCap,
      shortDesc: 'Evaluates explanation clarity, example density, and Q&A flow.',
      flowSteps: ['Teaching Segment', 'Pattern Detected', 'Dimension Evaluated', 'Teaching Insight'],
      demoClaim: 'Delivery Pattern: 6 code examples, 1:4 student Q&A interaction ratio',
      demoResult: 'Status: High Code Example Density · Strong Pacing',
      demoReference: '5-Dimension Pedagogical Clarity Framework',
      demoWhy: 'Provides objective feedback on teaching quality beyond simple attendance.'
    },
    {
      id: 4,
      title: 'Faculty Growth Guidance',
      question: 'What practical steps should faculty take next?',
      statusTag: 'Action Ready',
      color: 'amber',
      icon: Lightbulb,
      shortDesc: 'Turns detected teaching patterns into prioritized action items.',
      flowSteps: ['Teaching Gap Detected', 'Evidence Gathered', 'Priority Assigned', 'Recommendation Generated'],
      demoClaim: 'Detected Gap: 15-minute gap in active student comprehension checks',
      demoResult: 'Status: High Priority Action Identified · Timestamped Excerpt',
      demoReference: 'Timestamped Lecture Excerpt: min 24:15 - min 39:10',
      demoWhy: 'Converts detected teaching patterns into practical improvement steps.'
    },
    {
      id: 5,
      title: 'Evidence & Citations',
      question: 'Why does ClassroomIQ reach this conclusion?',
      statusTag: 'Evidence Linked',
      color: 'purple',
      icon: FileText,
      shortDesc: 'Attaches transcript snippets and textbook page citations to all findings.',
      flowSteps: ['Insight Generated', 'Transcript Segment', 'Reference Source', 'Citation Chain'],
      demoClaim: 'Verdict Proof: Multi-engine DAG reasoning chain & textbook citation',
      demoResult: 'Status: 100% Auditable Evidence Chain Attached',
      demoReference: 'Textbook PDF Page 142 & Audio Transcript Snippet #042',
      demoWhy: 'Enables faculty to verify and trust every system recommendation.'
    }
  ]

  const activeNode = outputNodes.find((n) => n.id === selectedOutput)

  return (
    <section id="faculty-outcomes" className="py-24 lg:py-36 border-t border-line bg-canvas relative overflow-hidden">
      {/* Ambient Glow */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -z-10 h-[650px] w-[950px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-tr from-brand/10 via-indigo-500/5 to-purple-500/10 blur-[150px]" />

      <div className="mx-auto max-w-7xl px-6 relative z-10">
        
        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <span className="text-xs sm:text-sm font-mono font-bold uppercase tracking-wider text-brand">
            FACULTY INTELLIGENCE OUTPUT
          </span>
          <h2 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-ink dark:text-white leading-tight">
            So, What Does a Faculty Member Actually Get?
          </h2>
          <p className="mt-4 text-lg sm:text-xl text-muted dark:text-slate-200 leading-relaxed font-bold">
            ClassroomIQ transforms a delivered lecture into structured, evidence-backed teaching intelligence that supports educator growth and institutional quality.
          </p>
        </div>

        {/* Master Interactive Visual Transformation Container */}
        <div className="rounded-3xl border border-line bg-surface/90 dark:bg-slate-900/90 p-8 sm:p-12 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.1)] backdrop-blur-xl space-y-12">
          
          {/* 3-Stage Visual Pipeline */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* 1. INPUT NODE */}
            <div className="lg:col-span-3 rounded-2xl border border-line bg-canvas p-6 shadow-soft space-y-4">
              <div className="flex items-center justify-between border-b border-line pb-3">
                <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider">
                  01 LECTURE INPUT
                </span>
                <Mic className="h-4 w-4 text-brand" />
              </div>

              <h4 className="font-extrabold text-lg text-ink dark:text-white">Lecture Analyzed</h4>

              <div className="space-y-2.5 text-xs font-bold text-slate-800 dark:text-slate-100">
                <div className="flex items-center gap-2.5 rounded-xl border border-line bg-surface p-2.5">
                  <Mic className="h-4 w-4 text-brand shrink-0" />
                  <span>Delivered Lecture Audio</span>
                </div>
                <div className="flex items-center gap-2.5 rounded-xl border border-line bg-surface p-2.5">
                  <BookOpen className="h-4 w-4 text-indigo-400 shrink-0" />
                  <span>Official Course Syllabus</span>
                </div>
                <div className="flex items-center gap-2.5 rounded-xl border border-line bg-surface p-2.5">
                  <Database className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Reference Materials</span>
                </div>
              </div>
            </div>

            {/* 2. TRANSFORMATION */}
            <div className="lg:col-span-3 flex flex-col items-center justify-center text-center space-y-3">
              <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider">
                02 INTELLIGENCE PIPELINE
              </span>

              <div className="w-full flex items-center justify-between gap-1 px-2 py-3 rounded-xl border border-brand/20 bg-brand-soft/30 text-[11px] font-mono text-brand font-bold">
                <span>LECTURE</span>
                <ArrowRight className="h-3 w-3 animate-pulse" />
                <span>GROUND</span>
                <ArrowRight className="h-3 w-3 animate-pulse" />
                <span>VERIFY</span>
              </div>

              <p className="text-xs text-muted dark:text-slate-300 font-bold max-w-xs">
                Passes through 5 connected engines to cross-reference speech against textbooks.
              </p>
            </div>

            {/* 3. CENTRAL FACULTY INTELLIGENCE REPORT OBJECT */}
            <div className="lg:col-span-6 rounded-3xl border border-brand/40 bg-gradient-to-b from-canvas via-surface to-canvas p-6 sm:p-8 shadow-2xl shadow-brand/10 text-center relative overflow-hidden">
              <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-brand via-indigo-500 to-teal-400" />
              
              <div className="inline-flex items-center gap-2 rounded-full bg-brand-soft px-4 py-1 text-xs font-mono font-bold text-brand mb-3 border border-brand/20">
                <Cpu className="h-3.5 w-3.5 text-brand" />
                <span>03 FACULTY REPORT OBJECT</span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-extrabold text-ink dark:text-white">Faculty Intelligence Report</h3>
              <p className="mt-2 text-xs sm:text-sm text-muted dark:text-slate-200 font-bold max-w-md mx-auto">
                Click any of the 5 connected output nodes below to explore its evidence chain and verification breakdown.
              </p>
            </div>

          </div>

          {/* 5 Connected Output Nodes (Teal Replace Emerald) */}
          <div className="space-y-4">
            <span className="text-xs font-mono font-bold text-teal-400 uppercase tracking-wider block text-center">
              CONNECTED INTELLIGENCE OUTPUT NODES (CLICK TO EXPLORE EVIDENCE)
            </span>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {outputNodes.map((node) => {
                const Icon = node.icon
                const isSelected = selectedOutput === node.id
                return (
                  <button
                    key={node.id}
                    onClick={() => setSelectedOutput(node.id)}
                    className={`group text-left rounded-2xl border p-5 transition-all duration-300 flex flex-col justify-between bg-surface ${
                      isSelected
                        ? 'border-brand shadow-float ring-2 ring-brand/30 -translate-y-1'
                        : 'border-line hover:border-brand/40 hover:-translate-y-0.5'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-soft text-brand group-hover:bg-brand group-hover:text-white transition">
                          <Icon className="h-5 w-5" />
                        </div>
                        <span className="text-[10px] font-mono font-bold text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded-md border border-teal-400/20">
                          {node.statusTag}
                        </span>
                      </div>

                      <h4 className="font-bold text-base sm:text-lg text-ink dark:text-white group-hover:text-brand transition leading-snug">
                        {node.title}
                      </h4>
                      <p className="mt-2 text-xs sm:text-sm text-muted dark:text-slate-300 leading-relaxed font-semibold line-clamp-2">
                        {node.shortDesc}
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-line/60 flex items-center justify-between text-xs font-bold text-brand">
                      <span>View Proof</span>
                      <ChevronRight className={`h-4 w-4 transition-transform ${isSelected ? 'translate-x-1' : 'opacity-40'}`} />
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

        </div>

      </div>

      {/* Progressive Disclosure Interactive Detail Modal */}
      <AnimatePresence>
        {selectedOutput !== null && activeNode && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ duration: 0.3 }}
              className="relative w-full max-w-2xl rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-10 shadow-2xl text-ink dark:text-white overflow-hidden space-y-6"
            >
              {/* Modal Top Bar */}
              <div className="flex items-center justify-between border-b border-line pb-4">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand text-white">
                    <activeNode.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-xs font-mono font-bold text-brand uppercase">
                      PRODUCT VERIFICATION DEMO
                    </span>
                    <h3 className="text-xl sm:text-2xl font-extrabold text-ink dark:text-white leading-none">
                      {activeNode.title}
                    </h3>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedOutput(null)}
                  className="rounded-xl border border-line p-2 text-muted dark:text-slate-200 hover:text-ink dark:hover:text-white hover:bg-canvas transition"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Step-by-Step Verification Flow */}
              <div className="space-y-3">
                <span className="text-xs font-mono text-muted dark:text-slate-300 uppercase tracking-wider block font-bold">
                  VERIFICATION PIPELINE FLOW:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono text-center">
                  {activeNode.flowSteps.map((step, idx) => (
                    <div key={idx} className="rounded-xl border border-line bg-canvas p-2.5">
                      <span className="text-[10px] text-brand font-bold block mb-0.5">STEP 0{idx + 1}</span>
                      <span className="font-bold text-ink dark:text-white">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Realistic Demo Data Card */}
              <div className="rounded-2xl border border-brand/20 bg-canvas p-5 space-y-3 shadow-inner">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-brand uppercase">PRODUCT DEMO DATA</span>
                  <span className="text-xs font-bold text-teal-400 bg-teal-500/10 px-2.5 py-0.5 rounded-full border border-teal-400/20">
                    {activeNode.statusTag}
                  </span>
                </div>

                <p className="text-xs sm:text-sm font-mono text-slate-800 dark:text-white bg-surface p-3 rounded-xl border border-line font-bold">
                  {activeNode.demoClaim}
                </p>

                <div className="space-y-1.5 text-xs text-muted dark:text-slate-200 font-bold">
                  <p className="text-teal-400 font-bold">{activeNode.demoResult}</p>
                  <p className="text-indigo-400 font-bold">{activeNode.demoReference}</p>
                  <p className="text-slate-200 font-semibold">{activeNode.demoWhy}</p>
                </div>
              </div>

              {/* Modal Bottom Controls */}
              <div className="flex items-center justify-between border-t border-line pt-4">
                <span className="text-xs font-mono text-muted dark:text-slate-300 font-bold">ClassroomIQ Evidence Engine</span>
                <button
                  onClick={() => setSelectedOutput(null)}
                  className="inline-flex h-10 items-center gap-2 rounded-xl bg-brand px-6 text-xs sm:text-sm font-bold text-white shadow-soft hover:bg-brand/90 transition"
                >
                  <span>Close Demo View</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  )
}
