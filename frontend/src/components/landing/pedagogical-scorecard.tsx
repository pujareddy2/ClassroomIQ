import { useState } from 'react'
import { GraduationCap, CheckCircle2, MessageSquare, BarChart2, Zap, Layers } from 'lucide-react'

export function PedagogicalScorecard() {
  const [hoveredDim, setHoveredDim] = useState<number | null>(null)

  const dimensions = [
    {
      id: 1,
      title: 'Explanation Clarity',
      desc: 'Monitors speaking rate (WPM), filler words, and clean definition structures.',
      score: '92 / 100',
      icon: MessageSquare
    },
    {
      id: 2,
      title: 'Example & Code Density',
      desc: 'Detects real-world and numerical code examples spoken with exact timestamps.',
      score: '88 / 100',
      icon: Layers
    },
    {
      id: 3,
      title: 'Q&A & Student Engagement',
      desc: 'Tracks faculty questions and student responses to assess classroom participation balance.',
      score: '85 / 100',
      icon: Zap
    },
    {
      id: 4,
      title: 'Pacing & Time Allocation',
      desc: 'Measures time allocated per topic versus expected syllabus duration.',
      score: '90 / 100',
      icon: BarChart2
    },
    {
      id: 5,
      title: 'Lecture Structural Flow',
      desc: 'Evaluates lecture introduction, concept transition smoothness, and summary quality.',
      score: '86 / 100',
      icon: GraduationCap
    }
  ]

  return (
    <section id="pedagogy" className="py-20 lg:py-28 border-t border-line bg-canvas">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Text & 5 Dimension Cards */}
          <div className="lg:col-span-6">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-brand">Pedagogical Framework</span>
            <h2 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl text-ink">
              Teaching Quality Is More Than Correctness.
            </h2>
            <p className="mt-4 text-muted text-sm sm:text-base leading-relaxed">
              ClassroomIQ evaluates faculty teaching performance across 5 core pedagogical dimensions to support continuous academic excellence.
            </p>

            <div className="mt-8 space-y-3">
              {dimensions.map((dim) => {
                const Icon = dim.icon
                const isHovered = hoveredDim === dim.id
                return (
                  <div
                    key={dim.id}
                    onMouseEnter={() => setHoveredDim(dim.id)}
                    onMouseLeave={() => setHoveredDim(null)}
                    className={`rounded-2xl border p-4 transition-all duration-300 ${
                      isHovered
                        ? 'border-brand bg-surface shadow-soft ring-1 ring-brand/20'
                        : 'border-line bg-surface/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="grid h-8 w-8 place-items-center rounded-lg bg-brand-soft text-brand">
                          <Icon className="h-4 w-4" />
                        </div>
                        <h3 className="font-bold text-sm text-ink">{dim.title}</h3>
                      </div>
                      <span className="font-mono text-xs font-bold text-brand">{dim.score}</span>
                    </div>
                    <p className="mt-2 text-xs text-muted leading-relaxed pl-11">{dim.desc}</p>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Right Column: Real Academic Classroom Photograph with 5-Dimension Radar Card Overlay */}
          <div className="lg:col-span-6 relative">
            <div className="rounded-3xl overflow-hidden border border-line bg-surface p-2.5 shadow-float group">
              <div className="relative rounded-2xl overflow-hidden aspect-[4/3]">
                {/* Real Authentic Classroom Discussion Image */}
                <img 
                  src="https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=80" 
                  alt="Real University Classroom Discussion & Student Engagement" 
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700"
                />
                
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/20 to-transparent pointer-events-none" />

                <div className="absolute bottom-4 left-4 right-4 rounded-xl border border-white/20 bg-slate-950/80 p-4 backdrop-blur-md text-white flex items-center justify-between shadow-lg">
                  <div>
                    <span className="block text-xs font-semibold">5-Dimension Pedagogical Radar</span>
                    <span className="text-[11px] text-slate-300">Clarity, Examples, Q&A, Pacing, Flow</span>
                  </div>
                  <div className="text-right">
                    <span className="block text-xs font-mono font-bold text-emerald-400">88/100 Overall Score</span>
                    <span className="text-[10px] text-slate-400">Verified Teaching Metric</span>
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
