import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Sparkles, 
  ShieldCheck, 
  BookOpenCheck, 
  GraduationCap, 
  Lightbulb, 
  FileText, 
  ChevronRight, 
  ChevronLeft, 
  X,
  Compass,
  CheckCircle2
} from 'lucide-react'

export function InteractiveTour() {
  const [isOpen, setIsOpen] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  const tourPoints = [
    {
      step: 1,
      title: 'Technical Claim Validation Engine',
      category: 'Fact-Checking & RAG Grounding',
      icon: ShieldCheck,
      color: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30',
      description: 'Fact-checks spoken lecture formulas and technical claims against indexed 384-d vector textbook passages.',
      sampleText: 'Spoken Claim: "LL(1) parsers build parse trees top-down with 1 lookahead token."',
      verdict: '✓ VERIFIED FACTUAL (Confidence: 0.96)',
      citation: 'Compilers Textbook (Sec 4.4, p. 218)',
      highlightPos: 'Top Left (Hero Analytics)'
    },
    {
      step: 2,
      title: 'Syllabus Topic Coverage Engine',
      category: 'Curriculum Alignment',
      icon: BookOpenCheck,
      color: 'text-blue-500 bg-blue-500/10 border-blue-500/30',
      description: 'Maps delivered transcript passages to official curriculum units (Unit ➔ Chapter ➔ Topic) and measures pacing.',
      sampleText: 'Unit 2: Syntax Analysis & Parsing (Expected: 45 mins | Actual: 40 mins)',
      verdict: '✓ COVERED (92% Syllabus Alignment)',
      citation: 'Course Syllabus Code: CS-302',
      highlightPos: 'Center Left (Topic Pacing)'
    },
    {
      step: 3,
      title: '5-Dimension Pedagogical Scorecard',
      category: 'Teaching Quality',
      icon: GraduationCap,
      color: 'text-indigo-500 bg-indigo-500/10 border-indigo-500/30',
      description: 'Evaluates explanation clarity, WPM pacing, real-world example density, student Q&A ratio, and structural flow.',
      sampleText: 'Explanation Clarity: 92% | Example Density: High (6 code examples) | Q&A Ratio: 1:4',
      verdict: '★ 88 / 100 Overall Score',
      citation: 'Pedagogical Quality Metric Framework',
      highlightPos: 'Center Right (Pedagogy Radar)'
    },
    {
      step: 4,
      title: 'Prioritized Faculty Recommendations',
      category: 'Actionable Growth',
      icon: Lightbulb,
      color: 'text-amber-500 bg-amber-500/10 border-amber-500/30',
      description: 'Synthesizes multi-engine findings into HIGH, MEDIUM, and LOW priority feedback items tied to lecture timestamps.',
      sampleText: 'HIGH Priority: "Increase student discussion time during complex grammar proofs."',
      verdict: '3 Actionable Items Generated',
      citation: 'Timestamp 24:15 Excerpt Link',
      highlightPos: 'Bottom Left (Growth Items)'
    },
    {
      step: 5,
      title: 'Transparent Explainable AI (XAI)',
      category: 'Auditable Evidence',
      icon: FileText,
      color: 'text-purple-500 bg-purple-500/10 border-purple-500/30',
      description: 'Eliminates black-box AI verdicts with a 6-component confidence breakdown, logical DAG reasoning steps, and page citations.',
      sampleText: 'Reasoning Step 4: "Matched transcript snippet to textbook passage with 0.94 cosine similarity."',
      verdict: 'Auditable DAG Reasoning Tree',
      citation: 'PDF Citation Engine',
      highlightPos: 'Bottom Right (XAI DAG)'
    }
  ]

  const activePoint = tourPoints[currentStep]
  const Icon = activePoint.icon

  return (
    <>
      {/* Floating Tour Launch Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 rounded-full bg-brand px-5 py-3 text-sm font-semibold text-white shadow-float transition hover:bg-brand/90 hover:scale-105 active:scale-95"
      >
        <Compass className="h-5 w-5 animate-spin-slow text-white" />
        <span>Explore Key Points</span>
        <span className="grid h-5 w-5 place-items-center rounded-full bg-white/20 text-[10px] font-bold">
          {tourPoints.length}
        </span>
      </button>

      {/* Interactive Spotlight Tour Modal */}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ duration: 0.3 }}
              className="relative w-full max-w-2xl rounded-3xl border border-line bg-surface p-6 sm:p-8 shadow-float text-ink overflow-hidden"
            >
              {/* Top Bar */}
              <div className="flex items-center justify-between border-b border-line pb-4">
                <div className="flex items-center gap-2">
                  <div className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-white">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <span className="text-xs font-mono font-bold text-brand uppercase">{activePoint.category}</span>
                    <h3 className="text-base font-extrabold text-ink leading-none mt-0.5">
                      Point {activePoint.step} of {tourPoints.length}: {activePoint.title}
                    </h3>
                  </div>
                </div>

                <button
                  onClick={() => setIsOpen(false)}
                  className="rounded-xl border border-line p-2 text-muted hover:text-ink hover:bg-canvas transition"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Point Content Body */}
              <div className="my-6 space-y-4">
                <div className={`flex items-start gap-4 rounded-2xl border p-4 ${activePoint.color}`}>
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-surface shadow-soft">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-ink">{activePoint.title}</h4>
                    <p className="mt-1 text-xs text-muted leading-relaxed">{activePoint.description}</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-canvas p-4 space-y-2 text-xs">
                  <span className="text-[10px] font-mono text-muted uppercase tracking-wider block">Live Scenario Data Sample:</span>
                  <p className="font-semibold text-ink italic">"{activePoint.sampleText}"</p>
                  <div className="flex items-center justify-between pt-2 border-t border-line/60">
                    <span className="font-bold text-emerald-500 flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5" /> {activePoint.verdict}
                    </span>
                    <span className="text-muted font-medium">Source: {activePoint.citation}</span>
                  </div>
                </div>
              </div>

              {/* Bottom Step Controls */}
              <div className="flex items-center justify-between border-t border-line pt-4">
                <div className="flex items-center gap-1.5">
                  {tourPoints.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => setCurrentStep(idx)}
                      className={`h-2 rounded-full transition-all ${
                        currentStep === idx ? 'w-6 bg-brand' : 'w-2 bg-line hover:bg-brand/50'
                      }`}
                    />
                  ))}
                </div>

                <div className="flex items-center gap-3">
                  <button
                    disabled={currentStep === 0}
                    onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
                    className="inline-flex h-9 items-center gap-1 rounded-xl border border-line px-3 text-xs font-semibold text-muted hover:text-ink disabled:opacity-40 transition"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    <span>Previous</span>
                  </button>

                  <button
                    onClick={() => {
                      if (currentStep < tourPoints.length - 1) {
                        setCurrentStep((prev) => prev + 1)
                      } else {
                        setIsOpen(false)
                      }
                    }}
                    className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-brand px-4 text-xs font-semibold text-white shadow-soft hover:bg-brand/90 transition"
                  >
                    <span>{currentStep < tourPoints.length - 1 ? 'Next Point' : 'Finish Tour'}</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  )
}
