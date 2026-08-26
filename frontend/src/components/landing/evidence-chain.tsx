import { CheckCircle2, ShieldCheck, FileText, BookOpenCheck, GitCommit } from 'lucide-react'

export function EvidenceChain() {
  const chainSteps = [
    {
      label: '01 Recommendation',
      title: 'Increase Student Discussion Time',
      desc: 'HIGH priority recommendation generated for Lecture Session #14.',
      icon: ShieldCheck,
      color: 'text-amber-500 bg-amber-500/10'
    },
    {
      label: '02 Logical Reasoning',
      title: 'DAG Step: Q&A Ratio Below Threshold',
      desc: 'Faculty talk time was 92% with only 1 student interaction prompt detected.',
      icon: GitCommit,
      color: 'text-brand bg-brand-soft'
    },
    {
      label: '03 Transcript Evidence',
      title: 'Timestamp 24:15 Snippet',
      desc: '"Let us move quickly to syntax trees without taking questions now."',
      icon: FileText,
      color: 'text-blue-500 bg-blue-500/10'
    },
    {
      label: '04 Reference Citation',
      title: 'Pedagogical Reference Standard',
      desc: 'Effective STEM Teaching Guidelines (Chapter 4, Section 2.1, p. 84).',
      icon: BookOpenCheck,
      color: 'text-purple-500 bg-purple-500/10'
    },
    {
      label: '05 Verifiable Verdict',
      title: '0.94 Explainability Confidence',
      desc: 'Verified by 6-component confidence breakdown DAG engine.',
      icon: CheckCircle2,
      color: 'text-emerald-500 bg-emerald-500/10'
    }
  ]

  return (
    <section id="explainability" className="py-20 lg:py-28 border-t border-line bg-surface/50">
      <div className="mx-auto max-w-7xl px-6">
        
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-brand">Explainable AI</span>
          <h2 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-ink">
            Every Insight Has Evidence Behind It.
          </h2>
          <p className="mt-4 text-muted text-sm sm:text-base leading-relaxed">
            ClassroomIQ replaces black-box AI opinions with an auditable evidence chain linking recommendations directly to transcript snippets and textbook citations.
          </p>
        </div>

        {/* Visual Evidence Chain Cards */}
        <div className="mt-14 grid grid-cols-1 md:grid-cols-5 gap-4 relative">
          {chainSteps.map((st, idx) => {
            const Icon = st.icon
            return (
              <div key={idx} className="rounded-2xl border border-line bg-canvas p-5 flex flex-col justify-between shadow-soft">
                <div>
                  <span className="text-[10px] font-mono font-bold text-brand uppercase">{st.label}</span>
                  <div className={`grid h-9 w-9 place-items-center rounded-xl mt-3 ${st.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <h3 className="mt-3 font-bold text-xs text-ink">{st.title}</h3>
                  <p className="mt-1.5 text-[11px] text-muted leading-relaxed line-clamp-3">"{st.desc}"</p>
                </div>

                <div className="mt-4 pt-3 border-t border-line/60 flex items-center justify-between text-[11px] font-medium text-brand">
                  <span>Step 0{idx + 1} Grounded</span>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                </div>
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}
