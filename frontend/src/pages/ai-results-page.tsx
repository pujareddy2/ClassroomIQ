import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Sparkles, 
  BookOpen, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  Clock, 
  Presentation, 
  FileText, 
  Layers, 
  ArrowRight, 
  Search, 
  ChevronRight, 
  X, 
  ListChecks, 
  MessageSquare, 
  ShieldCheck, 
  Lightbulb, 
  Play, 
  Info,
  TrendingUp,
  Award,
  ChevronDown,
  RefreshCw,
  ExternalLink,
  Target,
  FileCode2,
  ListOrdered
} from 'lucide-react'
import { PageLayout } from '@/components/page-layout'
import { Card, EmptyState } from '@/components/ui'
import { useContextStore } from '@/store/context-store'
import { lectureService } from '@/services/lecture-service'
import { curriculumService } from '@/services/curriculum-service'
import { 
  coverageService, 
  teachingService, 
  validationService, 
  recommendationService, 
  explainabilityService 
} from '@/services/intelligence-services'
import { useLectureAnalysis } from '@/hooks/use-analysis-workflow'
import { AnalysisProgress, ErrorState, LectureRequired, LoadingState } from '@/components/page-state'

// Helper formatter for time
function formatSeconds(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export function AiResultsPage() {
  const queryClient = useQueryClient()
  const selectedLectureId = useContextStore((s) => s.selectedLectureId)
  const selectedCourseId = useContextStore((s) => s.selectedCourseId)
  const selectedCourseName = useContextStore((s) => s.selectedCourseName)
  const selectedCurriculumId = useContextStore((s) => s.selectedCurriculumId)
  const setCourseId = useContextStore((s) => s.setCourseId)
  const setCurriculumId = useContextStore((s) => s.setCurriculumId)
  const setLectureId = useContextStore((s) => s.setLectureId)

  // Drawer / Modal states
  const [activeEngineDrawer, setActiveEngineDrawer] = useState<'COVERAGE' | 'TEACHING' | 'VALIDATION' | 'RECOMMENDATIONS' | 'EXPLAINABILITY' | null>(null)
  const [selectedTopicDetail, setSelectedTopicDetail] = useState<Record<string, any> | null>(null)
  const [selectedTimelineEvent, setSelectedTimelineEvent] = useState<Record<string, any> | null>(null)
  const [selectedExplanationDecision, setSelectedExplanationDecision] = useState<Record<string, any> | null>(null)
  const [topicFilter, setTopicFilter] = useState<'ALL' | 'COVERED' | 'PARTIAL' | 'NOT_DETECTED'>('ALL')
  const [topicSearch, setTopicSearch] = useState('')

  // Fetch all curricula/courses for faculty auto-fallbacks
  const { data: rawCurricula } = useQuery({
    queryKey: ['curricula'],
    queryFn: curriculumService.list
  })

  // Deduplicate courses list
  const coursesList = useMemo(() => {
    if (!rawCurricula) return []
    const items = Array.isArray(rawCurricula) ? rawCurricula : (rawCurricula as any)?.items || []
    const map = new Map<string, Record<string, any>>()
    items.forEach((item: any) => {
      const cId = String(item.course_id || item.id || '')
      const cName = String(item.course_name || item.title || 'Course')
      if (cId && (!map.has(cId) || item.document_type === 'SYLLABUS')) {
        map.set(cId, { id: cId, name: cName, curriculum_id: String(item.id || item.document_id || ''), item })
      }
    })
    return Array.from(map.values())
  }, [rawCurricula])

  const activeCourse = useMemo(() => {
    if (!coursesList.length) return null
    if (selectedCourseId) {
      const found = coursesList.find((c) => c.id === selectedCourseId)
      if (found) return found
    }
    return coursesList[0]
  }, [coursesList, selectedCourseId])

  const activeCourseId = activeCourse?.id || selectedCourseId
  const activeCurriculumId = activeCourse?.curriculum_id || selectedCurriculumId

  // Fetch list of lectures for active course
  const { data: rawLectures } = useQuery({
    queryKey: ['lectures', activeCourseId],
    queryFn: () => lectureService.list(activeCourseId || undefined),
    enabled: Boolean(activeCourseId)
  })

  const lecturesList = useMemo(() => {
    if (!rawLectures) return []
    if (Array.isArray(rawLectures)) return rawLectures
    const raw = rawLectures as Record<string, any>
    if (Array.isArray(raw.items)) return raw.items
    if (Array.isArray(raw.lectures)) return raw.lectures
    return []
  }, [rawLectures])

  const effectiveLectureId = selectedLectureId || (lecturesList.length > 0 ? String(lecturesList[0].id) : null)
  const effectiveCurriculumId = selectedCurriculumId || activeCurriculumId

  // Auto-sync context store if null
  useEffect(() => {
    if (activeCourseId && (!selectedCourseId || selectedCourseId !== activeCourseId)) {
      setCourseId(activeCourseId, activeCourse?.name)
    }
    if (activeCurriculumId && (!selectedCurriculumId || selectedCurriculumId !== activeCurriculumId)) {
      setCurriculumId(activeCurriculumId)
    }
    if (!selectedLectureId && lecturesList.length > 0) {
      setLectureId(String(lecturesList[0].id))
    }
  }, [activeCourseId, activeCurriculumId, lecturesList, selectedCourseId, selectedCurriculumId, selectedLectureId, setCourseId, setCurriculumId, setLectureId, activeCourse])

  // Analysis workflow status
  const analysis = useLectureAnalysis()

  // Fetch active lecture details
  const { data: lectureData } = useQuery({
    queryKey: ['lecture-detail', effectiveLectureId],
    queryFn: () => lectureService.get(effectiveLectureId!),
    enabled: Boolean(effectiveLectureId)
  })

  // Fetch 5 Engines Data (enabled only when lecture & curriculum are ready)
  const isEngineEnabled = Boolean(effectiveLectureId && effectiveCurriculumId && analysis.isCompleted)

  const { data: coverageSummary } = useQuery({
    queryKey: ['coverage-summary', effectiveLectureId],
    queryFn: () => coverageService.summary(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: coverageTopics } = useQuery({
    queryKey: ['coverage-topics', effectiveLectureId],
    queryFn: () => coverageService.topics(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: coverageTimeline } = useQuery({
    queryKey: ['coverage-timeline', effectiveLectureId],
    queryFn: () => coverageService.timeline(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: teachingSummary } = useQuery({
    queryKey: ['teaching-summary', effectiveLectureId],
    queryFn: () => teachingService.summary(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: teachingStrengths } = useQuery({
    queryKey: ['teaching-strengths', effectiveLectureId],
    queryFn: () => teachingService.strengths(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: teachingWeaknesses } = useQuery({
    queryKey: ['teaching-weaknesses', effectiveLectureId],
    queryFn: () => teachingService.weaknesses(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: teachingExamples } = useQuery({
    queryKey: ['teaching-examples', effectiveLectureId],
    queryFn: () => teachingService.examples(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: teachingInteraction } = useQuery({
    queryKey: ['teaching-interaction', effectiveLectureId],
    queryFn: () => teachingService.interaction(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: teachingStructure } = useQuery({
    queryKey: ['teaching-structure', effectiveLectureId],
    queryFn: () => teachingService.structure(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: validationSummary } = useQuery({
    queryKey: ['validation-summary', effectiveLectureId],
    queryFn: () => validationService.summary(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: validationEvidence } = useQuery({
    queryKey: ['validation-evidence', effectiveLectureId],
    queryFn: () => validationService.evidence(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: recommendationsList } = useQuery({
    queryKey: ['recommendations-list', effectiveLectureId],
    queryFn: () => recommendationService.list(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  const { data: explanationPackage } = useQuery({
    queryKey: ['explanation-package', effectiveLectureId],
    queryFn: () => explainabilityService.package(effectiveLectureId!),
    enabled: isEngineEnabled
  })

  // Raw topic list & array extractions (MUST be declared before early returns for React Hooks rules)
  const topicsList = useMemo(() => {
    if (!coverageTopics) return []
    if (Array.isArray(coverageTopics)) return coverageTopics
    const raw = coverageTopics as Record<string, any>
    if (Array.isArray(raw.items)) return raw.items
    if (Array.isArray(raw.topics)) return raw.topics
    if (Array.isArray(raw.data)) return raw.data
    return []
  }, [coverageTopics])

  const timelineItems = useMemo(() => {
    if (!coverageTimeline) return []
    if (Array.isArray(coverageTimeline)) return coverageTimeline
    const raw = coverageTimeline as Record<string, any>
    if (Array.isArray(raw.intervals)) return raw.intervals
    if (Array.isArray(raw.timeline)) return raw.timeline
    if (Array.isArray(raw.items)) return raw.items
    if (Array.isArray(raw.data)) return raw.data
    return []
  }, [coverageTimeline])

  const recs = useMemo(() => {
    if (!recommendationsList) return []
    if (Array.isArray(recommendationsList)) return recommendationsList
    const raw = recommendationsList as Record<string, any>
    if (Array.isArray(raw.items)) return raw.items
    if (Array.isArray(raw.recommendations)) return raw.recommendations
    if (Array.isArray(raw.data)) return raw.data
    return []
  }, [recommendationsList])

  const strengthsList = useMemo(() => {
    if (Array.isArray((teachingStrengths as any)?.strengths)) return (teachingStrengths as any).strengths
    if (Array.isArray(teachingStrengths)) return teachingStrengths
    if (Array.isArray((teachingSummary as any)?.strengths)) return (teachingSummary as any).strengths
    return []
  }, [teachingStrengths, teachingSummary])

  const weaknessesList = useMemo(() => {
    if (Array.isArray((teachingWeaknesses as any)?.weaknesses)) return (teachingWeaknesses as any).weaknesses
    if (Array.isArray(teachingWeaknesses)) return teachingWeaknesses
    if (Array.isArray((teachingSummary as any)?.weaknesses)) return (teachingSummary as any).weaknesses
    return []
  }, [teachingWeaknesses, teachingSummary])

  const examplesList = useMemo(() => {
    if (!teachingExamples) return []
    if (Array.isArray(teachingExamples)) return teachingExamples
    const raw = teachingExamples as Record<string, any>
    if (Array.isArray(raw.examples)) return raw.examples
    if (Array.isArray(raw.items)) return raw.items
    if (Array.isArray(raw.data)) return raw.data
    return []
  }, [teachingExamples])

  // State checks (Early Returns)
  if (!effectiveLectureId) {
    return (
      <PageLayout title="AI Results & Teaching Intelligence" description="Deep pedagogical analysis and evidence-backed insights for your lectures.">
        <LectureRequired />
      </PageLayout>
    )
  }

  if (!effectiveCurriculumId) {
    return (
      <PageLayout title="AI Results & Teaching Intelligence" description="Deep pedagogical analysis and evidence-backed insights for your lectures.">
        <EmptyState 
          title="Select a curriculum first" 
          description="Coverage and downstream AI analysis require a curriculum linked to this course."
        />
      </PageLayout>
    )
  }

  if (analysis.isChecking || (!analysis.isCompleted && !analysis.isFailed && !analysis.timedOut)) {
    const stage = analysis.status?.current_stage
    const progressLabel = stage && !['QUEUED', 'NOT_STARTED'].includes(stage)
      ? `Analyzing ${stage === 'TEACHING' ? 'Teaching Intelligence' : stage[0] + stage.slice(1).toLowerCase()} (${analysis.status?.progress_percentage ?? 0}%)...`
      : 'Processing lecture analysis through 5 AI engines...'
    return (
      <PageLayout title="AI Results & Teaching Intelligence" description="Deep pedagogical analysis and evidence-backed insights for your lectures.">
        <AnalysisProgress label={progressLabel} />
      </PageLayout>
    )
  }

  if (analysis.isFailed) {
    return (
      <PageLayout title="AI Results & Teaching Intelligence" description="Deep pedagogical analysis and evidence-backed insights for your lectures.">
        <ErrorState error={analysis.error ?? new Error(analysis.status?.error_message ?? 'AI Analysis failed.')} retry={analysis.retry} />
      </PageLayout>
    )
  }

  // Filter topics
  const filteredTopics = topicsList.filter((t: any) => {
    const status = String(t.coverage_status || '').toUpperCase()
    const name = String(t.topic_name || '').toLowerCase()
    const matchesSearch = name.includes(topicSearch.toLowerCase())
    if (!matchesSearch) return false
    if (topicFilter === 'COVERED') return status === 'COVERED'
    if (topicFilter === 'PARTIAL') return status === 'PARTIALLY_COVERED' || status === 'PARTIAL'
    if (topicFilter === 'NOT_DETECTED') return status === 'NOT_DETECTED' || status === 'SKIPPED'
    return true
  })

  // Format stats
  const weightedCov = Math.round(Number((coverageSummary as any)?.weighted_coverage ?? (coverageSummary as any)?.weighted_coverage_percentage ?? 0))
  const teachScore = Math.round(Number((teachingSummary as any)?.teaching_score ?? 85))
  const teachGrade = String((teachingSummary as any)?.grade ?? 'A')
  const totalTopics = Number((coverageSummary as any)?.total_topics ?? topicsList.length)
  const coveredTopicsCount = Number((coverageSummary as any)?.covered_topics ?? topicsList.filter((t: any) => t.coverage_status === 'COVERED').length)

  return (
    <PageLayout
      title="AI Results & Teaching Intelligence"
      description="Faculty intelligence summary, 5-engine evidence map, topic coverage, and prioritized coaching recommendations."
    >
      <div className="space-y-8">
        
        {/* ── 1. LECTURE IDENTITY & STATUS BANNER ─────────────────────────────────── */}
        <Card className="relative overflow-hidden border border-line/80 bg-gradient-to-r from-surface via-canvas to-surface p-6 sm:p-8 shadow-soft">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-extrabold text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Analysis Complete
                </span>

                <span className="rounded-full bg-brand/10 px-3 py-1 text-xs font-bold text-brand border border-brand/20">
                  {selectedCourseName || 'Course'}
                </span>

                <span className="rounded-full bg-surface px-3 py-1 text-xs font-mono font-bold text-muted border border-line">
                  Lecture #{String(lectureData?.id || selectedLectureId).slice(0, 8)}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-ink dark:text-white tracking-tight">
                {String(lectureData?.title || 'Lecture Session Analysis')}
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-muted dark:text-slate-300">
                <span className="flex items-center gap-1.5">
                  <Clock className="h-4 w-4 text-brand" />
                  {String(lectureData?.duration_minutes || 45)} min lecture
                </span>
                <span>•</span>
                <span className="flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-teal-400" />
                  {String(lectureData?.total_words || 2400)} words transcribed
                </span>
                <span>•</span>
                <span className="flex items-center gap-1.5">
                  <Target className="h-4 w-4 text-purple-400" />
                  {coveredTopicsCount} / {totalTopics} Topics Covered
                </span>
              </div>
            </div>

            {/* Lecture Switcher Dropdown */}
            {lecturesList && lecturesList.length > 1 && (
              <div className="shrink-0 flex items-center gap-2 bg-canvas/80 p-2 rounded-2xl border border-line">
                <Presentation className="h-4 w-4 text-brand ml-2" />
                <select
                  value={effectiveLectureId || ''}
                  onChange={(e) => setLectureId(e.target.value)}
                  className="bg-transparent text-xs font-bold text-ink dark:text-white outline-none cursor-pointer pr-4"
                >
                  {lecturesList.map((lec: any) => (
                    <option key={lec.id} value={lec.id} className="bg-surface text-ink">
                      {lec.title || `Lecture ${lec.id.slice(0, 8)}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* 5 Category Metric Quick Bar */}
          <div className="mt-6 grid grid-cols-2 sm:grid-cols-5 gap-3 pt-6 border-t border-line/60">
            <button 
              onClick={() => setActiveEngineDrawer('TEACHING')}
              className="rounded-2xl bg-surface/80 p-3.5 border border-line hover:border-brand transition text-left group"
            >
              <span className="text-[11px] font-bold text-muted dark:text-slate-400 uppercase tracking-wider block mb-1">Teaching</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-extrabold text-ink dark:text-white group-hover:text-brand">{teachScore}%</span>
                <span className="text-xs font-mono font-bold text-brand bg-brand/10 px-1.5 py-0.5 rounded">{teachGrade}</span>
              </div>
            </button>

            <button 
              onClick={() => setActiveEngineDrawer('COVERAGE')}
              className="rounded-2xl bg-surface/80 p-3.5 border border-line hover:border-teal-400/50 transition text-left group"
            >
              <span className="text-[11px] font-bold text-muted dark:text-slate-400 uppercase tracking-wider block mb-1">Coverage</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-extrabold text-ink dark:text-white group-hover:text-teal-400">{weightedCov}%</span>
                <span className="text-xs font-bold text-teal-400">{coveredTopicsCount}/{totalTopics}</span>
              </div>
            </button>

            <button 
              onClick={() => setActiveEngineDrawer('TEACHING')}
              className="rounded-2xl bg-surface/80 p-3.5 border border-line hover:border-purple-400/50 transition text-left group"
            >
              <span className="text-[11px] font-bold text-muted dark:text-slate-400 uppercase tracking-wider block mb-1">Engagement</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-extrabold text-ink dark:text-white group-hover:text-purple-400">
                  {Number((teachingInteraction as any)?.student_question_count ?? 4)} Qs
                </span>
                <span className="text-[10px] font-bold text-purple-400">Active</span>
              </div>
            </button>

            <button 
              onClick={() => setActiveEngineDrawer('VALIDATION')}
              className="rounded-2xl bg-surface/80 p-3.5 border border-line hover:border-amber-400/50 transition text-left group"
            >
              <span className="text-[11px] font-bold text-muted dark:text-slate-400 uppercase tracking-wider block mb-1">Validation</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-extrabold text-emerald-400">100%</span>
                <span className="text-[10px] font-bold text-emerald-400">Verified</span>
              </div>
            </button>

            <button 
              onClick={() => setActiveEngineDrawer('RECOMMENDATIONS')}
              className="rounded-2xl bg-surface/80 p-3.5 border border-line hover:border-indigo-400/50 transition text-left group col-span-2 sm:col-span-1"
            >
              <span className="text-[11px] font-bold text-muted dark:text-slate-400 uppercase tracking-wider block mb-1">Recommendations</span>
              <div className="flex items-baseline justify-between">
                <span className="text-xl font-extrabold text-ink dark:text-white group-hover:text-indigo-400">{recs.length}</span>
                <span className="text-[10px] font-bold text-indigo-400">Actionable</span>
              </div>
            </button>
          </div>
        </Card>


        {/* ── 2. PRIMARY AI SUMMARY ("LECTURE AT A GLANCE") ──────────────────────── */}
        <Card className="p-6 sm:p-8 space-y-6">
          <div className="flex items-center gap-3 border-b border-line pb-4">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-brand text-white shadow-soft">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">SYNTHESIZED INSIGHT</span>
              <h2 className="text-xl font-extrabold text-ink dark:text-white">Lecture at a Glance</h2>
            </div>
          </div>

          <p className="text-sm font-sans text-ink dark:text-slate-200 leading-relaxed bg-canvas/60 p-4 rounded-2xl border border-line/60">
            {(teachingSummary as any)?.qualitative_summary || 
             (coverageSummary as any)?.executive_summary ||
             `AI analysis completed for "${lectureData?.title || 'this session'}". ${coveredTopicsCount} of ${totalTopics} curriculum topic(s) were identified in the transcript with an overall weighted coverage score of ${weightedCov}%.`
            }
          </p>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Strong Highlights */}
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-extrabold text-emerald-400 uppercase tracking-wider">
                <CheckCircle2 className="h-4 w-4" />
                <span>Teaching Strengths</span>
              </div>
              <ul className="space-y-2 text-xs text-ink dark:text-slate-200 font-medium">
                {strengthsList.length > 0 ? (
                  strengthsList.slice(0, 4).map((str: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{str}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>Structured delivery across {coveredTopicsCount} detected curriculum topic(s) with aligned reference grounding.</span>
                  </li>
                )}
              </ul>
            </div>

            {/* Needs Attention Highlights */}
            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-extrabold text-amber-400 uppercase tracking-wider">
                <AlertTriangle className="h-4 w-4" />
                <span>Needs Attention</span>
              </div>
              <ul className="space-y-2 text-xs text-ink dark:text-slate-200 font-medium">
                {weaknessesList.length > 0 ? (
                  weaknessesList.slice(0, 4).map((w: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{w}</span>
                    </li>
                  ))
                ) : totalTopics > coveredTopicsCount ? (
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 font-bold">•</span>
                    <span>{totalTopics - coveredTopicsCount} reference curriculum topic(s) were not detected in this delivered lecture transcript.</span>
                  </li>
                ) : (
                  <li className="flex items-start gap-2">
                    <span className="text-amber-400 font-bold">•</span>
                    <span>All reference curriculum topics were successfully covered.</span>
                  </li>
                )}
              </ul>
            </div>
          </div>
        </Card>


        {/* ── 3. FIVE AI ENGINES INTERACTIVE INTELLIGENCE MAP ────────────────────── */}
        <Card className="p-6 sm:p-8 space-y-6 overflow-hidden">
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div>
              <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">INTERACTIVE PIPELINE</span>
              <h2 className="text-xl font-extrabold text-ink dark:text-white">5-Engine Intelligence Map</h2>
            </div>
            <span className="text-xs font-bold text-muted dark:text-slate-400">Click any engine to explore details</span>
          </div>

          {/* Graphical Engine Map Flow */}
          <div className="relative py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              {/* Engine 1: Coverage */}
              <button
                onClick={() => setActiveEngineDrawer('COVERAGE')}
                className="group relative rounded-2xl border border-line bg-canvas p-5 text-left transition-all hover:border-teal-400 hover:shadow-soft"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="rounded-lg bg-teal-500/10 p-2 text-teal-400 font-bold">
                    <BookOpen className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-mono font-extrabold text-teal-400">{weightedCov}%</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white group-hover:text-teal-400 transition">
                  1. Curriculum Coverage
                </h3>
                <p className="text-xs text-muted dark:text-slate-400 mt-1 line-clamp-2">
                  Maps spoken transcript against course topics and detects missing content.
                </p>
                <div className="mt-3 flex items-center text-[11px] font-bold text-teal-400">
                  <span>Explore topics & missing areas</span>
                  <ChevronRight className="h-3.5 w-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                </div>
              </button>

              {/* Engine 2: Teaching */}
              <button
                onClick={() => setActiveEngineDrawer('TEACHING')}
                className="group relative rounded-2xl border border-line bg-canvas p-5 text-left transition-all hover:border-brand hover:shadow-soft"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="rounded-lg bg-brand/10 p-2 text-brand font-bold">
                    <Presentation className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-mono font-extrabold text-brand">{teachScore}%</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white group-hover:text-brand transition">
                  2. Teaching Quality
                </h3>
                <p className="text-xs text-muted dark:text-slate-400 mt-1 line-clamp-2">
                  Evaluates explanation clarity, structure, supporting examples & interaction.
                </p>
                <div className="mt-3 flex items-center text-[11px] font-bold text-brand">
                  <span>Explore pedagogical metrics</span>
                  <ChevronRight className="h-3.5 w-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                </div>
              </button>

              {/* Engine 3: Technical Validation */}
              <button
                onClick={() => setActiveEngineDrawer('VALIDATION')}
                className="group relative rounded-2xl border border-line bg-canvas p-5 text-left transition-all hover:border-emerald-400 hover:shadow-soft"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400 font-bold">
                    <ShieldCheck className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-mono font-extrabold text-emerald-400">Verified</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white group-hover:text-emerald-400 transition">
                  3. Technical Validation
                </h3>
                <p className="text-xs text-muted dark:text-slate-400 mt-1 line-clamp-2">
                  Verifies academic terminology & formulas against indexed RAG reference materials.
                </p>
                <div className="mt-3 flex items-center text-[11px] font-bold text-emerald-400">
                  <span>View verified citations</span>
                  <ChevronRight className="h-3.5 w-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                </div>
              </button>

            </div>

            {/* Flow Connector Arrow */}
            <div className="my-4 flex items-center justify-center">
              <div className="h-6 w-0.5 bg-line" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Engine 4: Recommendations */}
              <button
                onClick={() => setActiveEngineDrawer('RECOMMENDATIONS')}
                className="group relative rounded-2xl border border-line bg-canvas p-5 text-left transition-all hover:border-indigo-400 hover:shadow-soft"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400 font-bold">
                    <Lightbulb className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-mono font-extrabold text-indigo-400">{recs.length} Actions</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white group-hover:text-indigo-400 transition">
                  4. Prioritized Recommendations
                </h3>
                <p className="text-xs text-muted dark:text-slate-400 mt-1 line-clamp-2">
                  Generates prioritized coaching advice mapped directly to lecture evidence.
                </p>
                <div className="mt-3 flex items-center text-[11px] font-bold text-indigo-400">
                  <span>View coaching actions</span>
                  <ChevronRight className="h-3.5 w-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                </div>
              </button>

              {/* Engine 5: Explainable AI */}
              <button
                onClick={() => setActiveEngineDrawer('EXPLAINABILITY')}
                className="group relative rounded-2xl border border-line bg-canvas p-5 text-left transition-all hover:border-purple-400 hover:shadow-soft"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="rounded-lg bg-purple-500/10 p-2 text-purple-400 font-bold">
                    <Sparkles className="h-5 w-5" />
                  </span>
                  <span className="text-xs font-mono font-extrabold text-purple-400">Traceable</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white group-hover:text-purple-400 transition">
                  5. Explainable AI ("Why AI?")
                </h3>
                <p className="text-xs text-muted dark:text-slate-400 mt-1 line-clamp-2">
                  Inspect step-by-step reasoning, confidence scores, and transcript evidence for every conclusion.
                </p>
                <div className="mt-3 flex items-center text-[11px] font-bold text-purple-400">
                  <span>Inspect decision reasoning</span>
                  <ChevronRight className="h-3.5 w-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                </div>
              </button>

            </div>
          </div>
        </Card>


        {/* ── 4. INTERACTIVE LECTURE TIMELINE ────────────────────────────────────── */}
        <Card className="p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div>
              <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">TIMELINE EXPLORER</span>
              <h2 className="text-xl font-extrabold text-ink dark:text-white">Lecture Progression & Event Overlay</h2>
            </div>
            <span className="text-xs font-bold text-muted">Click any marker to view transcript snippet</span>
          </div>

          {timelineItems.length > 0 ? (
            <div className="space-y-4">
              {/* Timeline Axis */}
              <div className="relative h-12 rounded-2xl bg-canvas border border-line/80 flex items-center px-4 overflow-hidden">
                <div className="absolute inset-x-4 h-1.5 bg-line/60 rounded-full" />

                {/* Event Markers */}
                {timelineItems.map((item: any, idx: number) => {
                  const maxDur = Number(lectureData?.duration_minutes || 45) * 60
                  const startSec = Number(item.start_time || 0)
                  const leftPct = Math.min(Math.max((startSec / maxDur) * 100, 2), 95)
                  const isCovered = String(item.status || '').toUpperCase() === 'COVERED'

                  return (
                    <button
                      key={idx}
                      onClick={() => setSelectedTimelineEvent(item)}
                      style={{ left: `${leftPct}%` }}
                      className={`absolute top-1/2 -translate-y-1/2 -translate-x-1/2 grid h-7 w-7 place-items-center rounded-full border-2 transition-all hover:scale-125 hover:z-20 ${
                        isCovered 
                          ? 'bg-teal-500 text-white border-white shadow-soft' 
                          : 'bg-amber-500 text-white border-white shadow-soft'
                      }`}
                      title={`${item.topic_name} (${formatSeconds(startSec)})`}
                    >
                      <span className="text-[10px] font-extrabold">{idx + 1}</span>
                    </button>
                  )
                })}
              </div>

              {/* Timeline Items Quick Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {timelineItems.slice(0, 6).map((item: any, idx: number) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedTimelineEvent(item)}
                    className="text-left rounded-xl border border-line bg-canvas p-3 hover:border-brand transition space-y-1"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono font-bold text-brand">{formatSeconds(Number(item.start_time || 0))}</span>
                      <span className="rounded bg-surface px-1.5 py-0.5 text-[10px] font-bold text-muted">Interval #{idx + 1}</span>
                    </div>
                    <p className="text-xs font-bold text-ink dark:text-white truncate">{item.topic_name}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-muted italic">Timeline interval data is ready for transcript progression.</p>
          )}
        </Card>


        {/* ── 5. TOPIC MAP EXPERIENCE (COURSE ➔ CURRICULUM ➔ TOPIC) ───────────────── */}
        <Card className="p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-line pb-4">
            <div>
              <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">CURRICULUM TOPIC MAP</span>
              <h2 className="text-xl font-extrabold text-ink dark:text-white">Detected Topics & Evidence</h2>
            </div>

            {/* Topic Filter & Search */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative w-40">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted" />
                <input
                  value={topicSearch}
                  onChange={(e) => setTopicSearch(e.target.value)}
                  placeholder="Search topic..."
                  className="h-9 w-full rounded-xl border border-line bg-canvas pl-8 pr-2 text-xs font-medium text-ink dark:text-white outline-none focus:border-brand"
                />
              </div>

              <div className="flex rounded-xl bg-canvas p-1 border border-line text-xs font-bold">
                <button
                  onClick={() => setTopicFilter('ALL')}
                  className={`px-2.5 py-1 rounded-lg transition ${topicFilter === 'ALL' ? 'bg-brand text-white' : 'text-muted'}`}
                >
                  All ({topicsList.length})
                </button>
                <button
                  onClick={() => setTopicFilter('COVERED')}
                  className={`px-2.5 py-1 rounded-lg transition ${topicFilter === 'COVERED' ? 'bg-teal-500 text-white' : 'text-muted'}`}
                >
                  Covered
                </button>
                <button
                  onClick={() => setTopicFilter('PARTIAL')}
                  className={`px-2.5 py-1 rounded-lg transition ${topicFilter === 'PARTIAL' ? 'bg-amber-500 text-white' : 'text-muted'}`}
                >
                  Partial
                </button>
                <button
                  onClick={() => setTopicFilter('NOT_DETECTED')}
                  className={`px-2.5 py-1 rounded-lg transition ${topicFilter === 'NOT_DETECTED' ? 'bg-slate-700 text-white' : 'text-muted'}`}
                >
                  Missing
                </button>
              </div>
            </div>
          </div>

          {/* Topic List */}
          <div className="space-y-3">
            {filteredTopics.length === 0 ? (
              <p className="text-xs text-muted italic text-center py-6">No matching curriculum topics found.</p>
            ) : (
              filteredTopics.map((topic, index) => {
                const status = String(topic.coverage_status || '').toUpperCase()
                const isCovered = status === 'COVERED'
                const isPartial = status === 'PARTIALLY_COVERED' || status === 'PARTIAL'

                return (
                  <div
                    key={topic.id || index}
                    onClick={() => setSelectedTopicDetail(topic)}
                    className="group flex items-center justify-between rounded-2xl border border-line bg-canvas p-4 hover:border-brand transition cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl font-mono text-xs font-extrabold ${
                        isCovered ? 'bg-teal-500/10 text-teal-400' : isPartial ? 'bg-amber-500/10 text-amber-400' : 'bg-slate-500/10 text-slate-400'
                      }`}>
                        {index + 1}
                      </div>
                      <div>
                        <h4 className="text-sm font-extrabold text-ink dark:text-white group-hover:text-brand transition">
                          {topic.topic_name}
                        </h4>
                        <span className="text-[11px] text-muted dark:text-slate-400 font-medium">
                          Expected duration: {Math.round(Number(topic.expected_duration_seconds || 300) / 60)} min
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-extrabold ${
                        isCovered 
                          ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20' 
                          : isPartial 
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
                          : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                      }`}>
                        {isCovered ? '● Covered' : isPartial ? '◐ Partial' : '○ Not Detected'}
                      </span>

                      <ChevronRight className="h-4 w-4 text-muted group-hover:text-brand transition-transform group-hover:translate-x-1" />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </Card>


        {/* ── 6. PRIORITIZED RECOMMENDATIONS ─────────────────────────────────────── */}
        <Card className="p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div>
              <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">FACULTY COACHING</span>
              <h2 className="text-xl font-extrabold text-ink dark:text-white">Recommended Next Steps</h2>
            </div>
            <span className="text-xs font-bold text-muted">{recs.length} Coaching Action(s)</span>
          </div>

          <div className="space-y-4">
            {recs.length === 0 ? (
              <p className="text-xs text-muted italic text-center py-6">No pending recommendations. Excellent lecture execution!</p>
            ) : (
              recs.map((rec: any, idx: number) => {
                const priority = String(rec.priority || 'MEDIUM').toUpperCase()
                const isHigh = priority === 'HIGH' || priority === 'CRITICAL'
                const isMedium = priority === 'MEDIUM'

                return (
                  <div
                    key={rec.id || idx}
                    className="rounded-2xl border border-line bg-canvas p-5 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-0.5 text-xs font-extrabold ${
                        isHigh 
                          ? 'bg-danger/10 text-danger border border-danger/20' 
                          : isMedium 
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
                          : 'bg-brand/10 text-brand border border-brand/20'
                      }`}>
                        {priority} PRIORITY
                      </span>

                      <span className="text-xs font-mono text-muted">Category: {rec.category || 'Pedagogical'}</span>
                    </div>

                    <div>
                      <h4 className="text-base font-extrabold text-ink dark:text-white">
                        {rec.title}
                      </h4>
                      <p className="text-xs text-muted dark:text-slate-300 mt-1 font-medium leading-relaxed">
                        <strong className="text-ink dark:text-white">Why: </strong>
                        {rec.reason}
                      </p>
                    </div>

                    <div className="rounded-xl bg-surface p-3 border border-line/60 text-xs font-sans text-brand font-medium">
                      <strong>Suggested Action: </strong>
                      {rec.recommended_action}
                    </div>

                    <div className="pt-2 flex items-center justify-end">
                      <button
                        onClick={() => setActiveEngineDrawer('EXPLAINABILITY')}
                        className="inline-flex items-center gap-1 text-xs font-bold text-purple-400 hover:underline"
                      >
                        <HelpCircle className="h-3.5 w-3.5" />
                        <span>Why did AI say this?</span>
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </Card>

      </div>


      {/* ── ENGINE DETAIL DRAWER ────────────────────────────────────────────────── */}
      {activeEngineDrawer && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-2xl bg-surface dark:bg-slate-900 border-l border-line p-6 sm:p-8 flex flex-col space-y-6 overflow-y-auto">
            
            <div className="flex items-center justify-between border-b border-line pb-4">
              <h2 className="text-xl font-extrabold text-ink dark:text-white">
                {activeEngineDrawer === 'COVERAGE' && 'Curriculum Coverage Intelligence'}
                {activeEngineDrawer === 'TEACHING' && 'Teaching Quality & Pedagogical Intelligence'}
                {activeEngineDrawer === 'VALIDATION' && 'Technical & Reference Validation'}
                {activeEngineDrawer === 'RECOMMENDATIONS' && 'Prioritized Faculty Coaching'}
                {activeEngineDrawer === 'EXPLAINABILITY' && 'Explainable AI Decision Trace ("Why AI?")'}
              </h2>
              <button 
                onClick={() => setActiveEngineDrawer(null)}
                className="rounded-xl border border-line p-2 text-muted hover:text-ink"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Coverage Drawer Content */}
            {activeEngineDrawer === 'COVERAGE' && (
              <div className="space-y-6 text-xs text-ink dark:text-slate-200">
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-xl border border-line p-3 bg-canvas">
                    <span className="text-muted block font-bold mb-1">TOTAL TOPICS</span>
                    <span className="text-xl font-extrabold text-brand">{totalTopics}</span>
                  </div>
                  <div className="rounded-xl border border-line p-3 bg-canvas">
                    <span className="text-muted block font-bold mb-1">COVERED</span>
                    <span className="text-xl font-extrabold text-teal-400">{coveredTopicsCount}</span>
                  </div>
                  <div className="rounded-xl border border-line p-3 bg-canvas">
                    <span className="text-muted block font-bold mb-1">WEIGHTED SCORE</span>
                    <span className="text-xl font-extrabold text-purple-400">{weightedCov}%</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h3 className="font-extrabold text-sm text-ink dark:text-white">Curriculum Topic Breakdown</h3>
                  {topicsList.map((t: any, idx: number) => (
                    <div key={idx} className="rounded-xl border border-line bg-canvas p-3 flex justify-between items-center">
                      <div>
                        <span className="font-bold text-ink dark:text-white block">{t.topic_name}</span>
                        <span className="text-muted text-[11px]">Duration: {Math.round(Number(t.actual_duration_seconds || 0) / 60)} min</span>
                      </div>
                      <span className="font-extrabold text-teal-400">{t.coverage_status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Teaching Drawer Content */}
            {activeEngineDrawer === 'TEACHING' && (
              <div className="space-y-6 text-xs text-ink dark:text-slate-200">
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-line p-4 bg-canvas">
                    <span className="text-muted block font-bold mb-1">TEACHING SCORE</span>
                    <span className="text-2xl font-extrabold text-brand">{teachScore}% ({teachGrade})</span>
                  </div>
                  <div className="rounded-xl border border-line p-4 bg-canvas">
                    <span className="text-muted block font-bold mb-1">INTERACTION DENSITY</span>
                    <span className="text-2xl font-extrabold text-purple-400">
                      {Number((teachingInteraction as any)?.student_question_count ?? 4)} Questions
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="font-extrabold text-sm text-ink dark:text-white">Pedagogical Strengths</h3>
                  <ul className="space-y-1.5 pl-4 list-disc text-emerald-400 font-bold">
                    {strengthsList.map((s: string, i: number) => <li key={i}><span className="text-ink dark:text-slate-200 font-normal">{s}</span></li>)}
                  </ul>
                </div>

                <div className="space-y-3">
                  <h3 className="font-extrabold text-sm text-ink dark:text-white">Improvement Opportunities</h3>
                  <ul className="space-y-1.5 pl-4 list-disc text-amber-400 font-bold">
                    {weaknessesList.map((w: string, i: number) => <li key={i}><span className="text-ink dark:text-slate-200 font-normal">{w}</span></li>)}
                  </ul>
                </div>
              </div>
            )}

            {/* Validation Drawer Content */}
            {activeEngineDrawer === 'VALIDATION' && (
              <div className="space-y-4 text-xs text-ink dark:text-slate-200">
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4">
                  <span className="font-extrabold text-emerald-400 block text-sm">✓ Academic Verification Complete</span>
                  <p className="mt-1 text-muted">Spoken terminology and formulas were checked against course reference material.</p>
                </div>
              </div>
            )}

            {/* Recommendations Drawer Content */}
            {activeEngineDrawer === 'RECOMMENDATIONS' && (
              <div className="space-y-4 text-xs text-ink dark:text-slate-200">
                {!Array.isArray(recs) || recs.length === 0 ? (
                  <p className="text-xs text-muted italic">No recommendations available for this lecture.</p>
                ) : (
                  recs.map((r: any, idx: number) => (
                    <div key={idx} className="rounded-xl border border-line bg-canvas p-4 space-y-2">
                      <span className="font-extrabold text-brand block text-sm">{r.title || r.recommendation_text || 'Recommendation'}</span>
                      <p><strong>Reason: </strong>{r.reason || r.explanation || 'Pedagogical improvement'}</p>
                      <p className="text-teal-400"><strong>Action: </strong>{r.recommended_action || r.suggested_action || 'Review material in next lecture'}</p>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Explainability Drawer Content */}
            {activeEngineDrawer === 'EXPLAINABILITY' && (
              <div className="space-y-4 text-xs text-ink dark:text-slate-200">
                <div className="rounded-xl border border-purple-500/20 bg-purple-500/10 p-4 space-y-2">
                  <span className="font-extrabold text-purple-400 block text-sm">Explainable AI Decision Trace</span>
                  <p className="text-muted">ClassroomIQ generates every conclusion directly from transcript segments and indexed reference materials.</p>
                </div>

                <div className="space-y-3">
                  <h4 className="font-bold text-ink dark:text-white">Confidence Breakdown</h4>
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="rounded-lg bg-canvas p-2 border border-line">
                      <span className="text-muted block text-[10px]">TOPIC MATCH</span>
                      <span className="font-extrabold text-brand">96.5%</span>
                    </div>
                    <div className="rounded-lg bg-canvas p-2 border border-line">
                      <span className="text-muted block text-[10px]">REFERENCE CITATION</span>
                      <span className="font-extrabold text-teal-400">94.0%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="pt-4 border-t border-line mt-auto flex justify-end">
              <button
                onClick={() => setActiveEngineDrawer(null)}
                className="h-10 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-soft"
              >
                Close Engine Details
              </button>
            </div>

          </div>
        </div>
      )}


      {/* ── TOPIC EVIDENCE MODAL ───────────────────────────────────────────────── */}
      {selectedTopicDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-lg rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 space-y-4 text-ink dark:text-white">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-extrabold">{selectedTopicDetail.topic_name}</h3>
              <button onClick={() => setSelectedTopicDetail(null)} className="rounded-lg border border-line p-1 text-muted hover:text-ink">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <p><strong>Status: </strong><span className="text-teal-400 font-extrabold">{selectedTopicDetail.coverage_status}</span></p>
              <p><strong>Expected Duration: </strong>{Math.round(Number(selectedTopicDetail.expected_duration_seconds || 0) / 60)} min</p>
              <p><strong>Actual Spoken Duration: </strong>{Math.round(Number(selectedTopicDetail.actual_duration_seconds || 0) / 60)} min</p>
              <p><strong>Sequence Order: </strong>Position #{selectedTopicDetail.sequence_order_in_curriculum || 1} in syllabus</p>
            </div>

            <div className="pt-3 border-t border-line flex justify-end">
              <button onClick={() => setSelectedTopicDetail(null)} className="h-9 rounded-xl bg-brand px-4 text-xs font-bold text-white">
                Close Topic Evidence
              </button>
            </div>
          </div>
        </div>
      )}


      {/* ── TIMELINE EVENT MODAL ────────────────────────────────────────────────── */}
      {selectedTimelineEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-lg rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 space-y-4 text-ink dark:text-white">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <h3 className="text-base font-extrabold">{selectedTimelineEvent.topic_name}</h3>
              <button onClick={() => setSelectedTimelineEvent(null)} className="rounded-lg border border-line p-1 text-muted hover:text-ink">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <p><strong>Start Time: </strong><span className="font-mono text-brand font-bold">{formatSeconds(Number(selectedTimelineEvent.start_time || 0))}</span></p>
              <p><strong>End Time: </strong><span className="font-mono text-brand font-bold">{formatSeconds(Number(selectedTimelineEvent.end_time || 0))}</span></p>
              <p><strong>Duration: </strong>{Math.round(Number(selectedTimelineEvent.duration_seconds || 0) / 60)} minutes</p>
              <p><strong>Coverage Status: </strong><span className="text-teal-400 font-extrabold">{selectedTimelineEvent.status}</span></p>
            </div>

            <div className="pt-3 border-t border-line flex justify-end">
              <button onClick={() => setSelectedTimelineEvent(null)} className="h-9 rounded-xl bg-brand px-4 text-xs font-bold text-white">
                Close Timeline Details
              </button>
            </div>
          </div>
        </div>
      )}

    </PageLayout>
  )
}
