import { useState } from 'react'
import { CheckCircle2, BookOpenCheck, Activity, Award } from 'lucide-react'

export function LiveAnalysis() {
  const [demoScenario, setDemoScenario] = useState<'compiler' | 'sorting' | 'quantum'>('compiler')

  const scenarios = {
    compiler: {
      title: 'Compiler Design — Lexical & Syntax Analysis',
      lecture: 'Session #14: Context-Free Grammars & LL(1) Parsing',
      claim: 'LL(1) parsers build the parse tree top-down with one lookahead token.',
      status: 'VERIFIED FACTUAL',
      confidence: '0.96',
      citation: 'Compilers: Principles, Techniques, & Tools (Sec 4.4, p. 218)',
      coverage: 'Unit 2: Syntax Analysis (100% Covered)',
      pacing: '40 minutes (Optimal)',
      errors: '0 Technical Errors'
    },
    sorting: {
      title: 'Data Structures — Algorithm Complexity',
      lecture: 'Session #08: QuickSort Partitioning & Master Theorem',
      claim: 'Worst-case time complexity of QuickSort occurs when the pivot selection is unbalanced.',
      status: 'VERIFIED FACTUAL',
      confidence: '0.98',
      citation: 'Introduction to Algorithms (CLRS, Chapter 7, p. 174)',
      coverage: 'Unit 3: Sorting Algorithms (85% Covered)',
      pacing: '45 minutes (Optimal)',
      errors: '0 Technical Errors'
    },
    quantum: {
      title: 'Quantum Physics — Superposition & Qubits',
      lecture: 'Session #03: Bloch Sphere Representations',
      claim: 'Hadamard gates transform standard basis states into equal superposition.',
      status: 'VERIFIED FACTUAL',
      confidence: '0.95',
      citation: 'Quantum Computation & Quantum Information (Sec 1.3, p. 18)',
      coverage: 'Unit 1: Quantum Logic Gates (92% Covered)',
      pacing: '38 minutes (Optimal)',
      errors: '0 Technical Errors'
    }
  }

  const current = scenarios[demoScenario]

  return (
    <section id="demo" className="py-20 lg:py-28 border-t border-line bg-surface/40">
      <div className="mx-auto max-w-7xl px-6">
        
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-brand">Live Demonstration</span>
          <h2 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-ink">
            See ClassroomIQ Think Through a Lecture
          </h2>
          <p className="mt-4 text-muted text-sm sm:text-base leading-relaxed">
            Select a real academic scenario below to observe RAG claim validation and textbook grounding.
          </p>
        </div>

        {/* Domain Selector Buttons */}
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          {[
            { id: 'compiler', label: 'Compiler Design' },
            { id: 'sorting', label: 'Data Structures' },
            { id: 'quantum', label: 'Quantum Physics' }
          ].map((sc) => (
            <button
              key={sc.id}
              onClick={() => setDemoScenario(sc.id as typeof demoScenario)}
              className={`rounded-xl px-5 py-2.5 text-sm font-semibold transition ${
                demoScenario === sc.id
                  ? 'bg-brand text-white shadow-soft'
                  : 'border border-line bg-surface text-muted hover:text-ink'
              }`}
            >
              {sc.label}
            </button>
          ))}
        </div>

        {/* Live Scenario Inspector Card */}
        <div className="mt-10 rounded-3xl border border-line bg-surface p-6 sm:p-10 shadow-float">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div>
              <span className="inline-block rounded-md bg-brand-soft px-3 py-1 text-xs font-bold text-brand">
                {current.lecture}
              </span>
              <h3 className="mt-3 text-2xl font-extrabold text-ink">{current.title}</h3>
              
              <div className="mt-6 rounded-2xl border border-line bg-canvas p-4">
                <span className="text-[11px] font-mono text-muted uppercase tracking-wider block mb-1">Spoken Technical Claim:</span>
                <p className="text-sm font-medium italic text-ink">"{current.claim}"</p>
              </div>

              <div className="mt-4 space-y-2.5 text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">
                    {current.status} (Confidence: {current.confidence})
                  </span>
                </div>
                <div className="flex items-center gap-2 text-muted">
                  <BookOpenCheck className="h-4 w-4 text-brand" />
                  <span>Reference: {current.citation}</span>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-line bg-canvas p-6 space-y-4">
              <h4 className="text-sm font-bold text-ink flex items-center justify-between">
                <span>Syllabus Alignment & Metrics</span>
                <Activity className="h-4 w-4 text-brand" />
              </h4>

              <div className="space-y-3 text-xs">
                <div>
                  <div className="flex justify-between font-medium mb-1">
                    <span className="text-muted">Unit Coverage</span>
                    <span className="text-brand font-bold">{current.coverage}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-line overflow-hidden">
                    <div className="h-full bg-brand rounded-full w-[95%]" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="rounded-xl border border-line bg-surface p-3 text-center">
                    <span className="block text-lg font-bold text-ink">{current.pacing}</span>
                    <span className="text-[11px] text-muted">Delivered Pacing</span>
                  </div>
                  <div className="rounded-xl border border-line bg-surface p-3 text-center">
                    <span className="block text-lg font-bold text-emerald-500">{current.errors}</span>
                    <span className="text-[11px] text-muted">Misconceptions</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  )
}
