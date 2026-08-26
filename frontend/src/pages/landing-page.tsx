import { Navbar } from '@/components/landing/navbar'
import { Hero } from '@/components/landing/hero'
import { SystemInputOutput } from '@/components/landing/system-input-output'
import { FiveEnginesPipeline } from '@/components/landing/five-engines-pipeline'
import { HowItWorks } from '@/components/landing/how-it-works'
import { FacultyOutcomes } from '@/components/landing/faculty-outcomes'
import { WhyClassroomIQ } from '@/components/landing/why-classroomiq'
import { CTASection } from '@/components/landing/cta-section'
import { Footer } from '@/components/landing/footer'

export function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas text-ink antialiased selection:bg-brand selection:text-white">
      <Navbar />
      <main>
        {/* Preserved Hero Section */}
        <Hero />

        {/* Level 1: What ClassroomIQ Receives & Transforms */}
        <SystemInputOutput />

        {/* Level 2: Five Intelligence Engines Connected Pipeline */}
        <FiveEnginesPipeline />

        {/* Level 3: Visual Process Story (Real Photography + Interactive Steps) */}
        <HowItWorks />

        {/* Level 4: Human Value & Faculty Outcomes */}
        <FacultyOutcomes />

        {/* Level 5: Institutional Trust & Final Call to Action */}
        <WhyClassroomIQ />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
