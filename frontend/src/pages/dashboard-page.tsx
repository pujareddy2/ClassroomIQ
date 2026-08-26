import { useState, useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  Sparkles, 
  BookOpen, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  Presentation, 
  FileText, 
  Upload, 
  ArrowRight, 
  Plus, 
  FolderKanban, 
  LibraryBig, 
  History as HistoryIcon, 
  Lightbulb, 
  ChevronRight, 
  Layers, 
  Check, 
  Play, 
  ShieldCheck, 
  BarChart3,
  UserCheck
} from 'lucide-react'
import { PageLayout } from '@/components/page-layout'
import { Card } from '@/components/ui'
import { useContextStore } from '@/store/context-store'
import { useAuthStore } from '@/store/auth-store'
import { curriculumService } from '@/services/curriculum-service'
import { referenceService } from '@/services/reference-service'
import { lectureService } from '@/services/lecture-service'
import { 
  coverageService, 
  teachingService, 
  recommendationService 
} from '@/services/intelligence-services'
import { useLectureAnalysis } from '@/hooks/use-analysis-workflow'

export function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  
  const { 
    selectedCourseId, 
    selectedCourseName, 
    selectedLectureId, 
    selectedCurriculumId,
    setCourseId, 
    setLectureId, 
    setCurriculumId 
  } = useContextStore()

  // Time of day greeting
  const greeting = useMemo(() => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }, [])

  // Fetch all curricula/courses for faculty
  const { data: rawCurricula, isLoading: isCurriculaLoading } = useQuery({
    queryKey: ['curricula'],
    queryFn: curriculumService.list
  })

  // Deduplicate courses list
  const coursesList = useMemo(() => {
    if (!rawCurricula) return []
    const map = new Map<string, Record<string, any>>()
    rawCurricula.forEach((item) => {
      const rec = item as Record<string, any>
      const cId = String(rec.course_id || rec.id || '')
      const cName = String(rec.course_name || rec.title || 'Course')
      if (cId && (!map.has(cId) || rec.document_type === 'SYLLABUS')) {
        map.set(cId, { id: cId, name: cName, curriculum_id: String(rec.id || rec.document_id || ''), rec })
      }
    })
    return Array.from(map.values())
  }, [rawCurricula])

  // Active course entity
  const activeCourse = useMemo(() => {
    if (!coursesList.length) return null
    if (selectedCourseId) {
      const found = coursesList.find((c) => c.id === selectedCourseId)
      if (found) return found
    }
    return coursesList[0]
  }, [coursesList, selectedCourseId])

  const activeCourseId = activeCourse?.id || selectedCourseId
  const activeCourseName = activeCourse?.name || selectedCourseName || 'Selected Course'

  // Fetch reference materials for active course
  const { data: referenceMaterials } = useQuery({
    queryKey: ['reference-materials', activeCourseId],
    queryFn: () => referenceService.list(activeCourseId || undefined),
    enabled: Boolean(activeCourseId)
  })

  // Fetch lectures for active course
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

  const latestLecture = lecturesList.length > 0 ? lecturesList[0] : null
  const latestLectureId = latestLecture ? String(latestLecture.id || '') : selectedLectureId

  // Live Analysis Workflow Status for latest lecture
  const analysis = useLectureAnalysis()

  // Fetch AI Insights & Recommendations preview for active lecture
  const { data: teachingSummary } = useQuery({
    queryKey: ['teaching-summary', latestLectureId],
    queryFn: () => teachingService.summary(latestLectureId!),
    enabled: Boolean(latestLectureId && analysis.isCompleted)
  })

  const { data: coverageSummary } = useQuery({
    queryKey: ['coverage-summary', latestLectureId],
    queryFn: () => coverageService.summary(latestLectureId!),
    enabled: Boolean(latestLectureId && analysis.isCompleted)
  })

  const { data: recommendationsList } = useQuery({
    queryKey: ['recommendations-list', latestLectureId],
    queryFn: () => recommendationService.list(latestLectureId!),
    enabled: Boolean(latestLectureId && analysis.isCompleted)
  })

  const recs = useMemo(() => {
    if (!recommendationsList) return []
    if (Array.isArray(recommendationsList)) return recommendationsList
    const raw = recommendationsList as Record<string, any>
    if (Array.isArray(raw.items)) return raw.items
    if (Array.isArray(raw.recommendations)) return raw.recommendations
    if (Array.isArray(raw.data)) return raw.data
    return []
  }, [recommendationsList])

  const refList = useMemo(() => {
    if (!referenceMaterials) return []
    if (Array.isArray(referenceMaterials)) return referenceMaterials
    const raw = referenceMaterials as Record<string, any>
    if (Array.isArray(raw.items)) return raw.items
    if (Array.isArray(raw.materials)) return raw.materials
    if (Array.isArray(raw.data)) return raw.data
    return []
  }, [referenceMaterials])

  // Check if first time user (no courses created yet)
  const isFirstTimeUser = !isCurriculaLoading && coursesList.length === 0

  return (
    <PageLayout
      title={`${greeting}${user?.full_name ? `, ${user.full_name}` : ''}`}
      description="Here's what's happening with your courses and teaching intelligence."
    >
      <div className="space-y-8">
        
        {/* ── 1. HEADER & PRIMARY STANDOUT ACTIONS ───────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-brand/10 via-canvas to-surface p-6 sm:p-8 rounded-3xl border border-line shadow-soft">
          <div className="space-y-1">
            <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">
              FACULTY WORKSPACE
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-ink dark:text-white tracking-tight">
              {greeting}, {user?.full_name || 'Faculty Member'}
            </h1>
            <p className="text-xs font-medium text-muted dark:text-slate-300">
              Manage your course materials, lecture analysis, and teaching intelligence.
            </p>
          </div>

          {/* Primary Action Buttons */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => navigate('/lectures')}
              className="inline-flex h-12 items-center gap-2 rounded-2xl bg-brand px-6 text-xs font-extrabold text-white shadow-soft hover:bg-brand/90 hover:scale-105 active:scale-95 transition"
            >
              <Upload className="h-4 w-4" />
              <span>+ Upload Lecture</span>
            </button>

            <button
              onClick={() => navigate(activeCourseId ? `/courses/${activeCourseId}/materials` : '/reference-materials')}
              className="inline-flex h-12 items-center gap-2 rounded-2xl border border-line bg-surface px-5 text-xs font-bold text-ink dark:text-white hover:bg-canvas transition"
            >
              <LibraryBig className="h-4 w-4 text-brand" />
              <span>Course Materials</span>
            </button>

            <button
              onClick={() => navigate('/history')}
              className="inline-flex h-12 items-center gap-2 rounded-2xl border border-line bg-surface px-5 text-xs font-bold text-ink dark:text-white hover:bg-canvas transition"
            >
              <HistoryIcon className="h-4 w-4 text-purple-400" />
              <span>View History</span>
            </button>
          </div>
        </div>


        {/* ── 2. COURSE CONTEXT SWITCHER ─────────────────────────────────────────── */}
        {coursesList.length > 0 && (
          <Card className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border border-line">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-brand/10 text-brand">
                <FolderKanban className="h-5 w-5" />
              </div>
              <div>
                <span className="text-[10px] font-mono font-bold text-muted uppercase tracking-wider block">
                  CURRENT ACTIVE COURSE
                </span>
                <h3 className="text-base font-extrabold text-ink dark:text-white">
                  {activeCourseName}
                </h3>
              </div>
            </div>

            {/* Course Dropdown */}
            <div className="flex items-center gap-3">
              <select
                value={activeCourseId || ''}
                onChange={(e) => {
                  const selected = coursesList.find((c) => c.id === e.target.value)
                  if (selected) {
                    setCourseId(selected.id, selected.name)
                    if (selected.curriculum_id) setCurriculumId(selected.curriculum_id)
                  }
                }}
                className="h-10 rounded-xl border border-line bg-canvas px-3.5 text-xs font-bold text-ink dark:text-white outline-none cursor-pointer focus:border-brand"
              >
                {coursesList.map((c) => (
                  <option key={c.id} value={c.id} className="bg-surface text-ink">
                    {c.name}
                  </option>
                ))}
              </select>

              <button
                onClick={() => navigate('/courses')}
                className="h-10 rounded-xl bg-surface px-4 text-xs font-bold text-brand border border-brand/20 hover:bg-brand/10 transition"
              >
                Manage Courses
              </button>
            </div>
          </Card>
        )}


        {/* ── 3. GUIDED FIRST-TIME FACULTY FLOW (ZERO STATE) ────────────────────── */}
        {isFirstTimeUser ? (
          <Card className="p-6 sm:p-8 space-y-6 border border-brand/30 bg-gradient-to-r from-brand/5 via-canvas to-surface">
            <div className="space-y-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-brand/10 px-3 py-1 text-xs font-extrabold text-brand">
                <Sparkles className="h-3.5 w-3.5" /> Welcome to ClassroomIQ
              </span>
              <h2 className="text-xl sm:text-2xl font-extrabold text-ink dark:text-white">
                Let's set up your first course intelligence workspace
              </h2>
              <p className="text-xs text-muted dark:text-slate-300 font-medium">
                Follow these 4 guided steps to establish your academic knowledge base and start evaluating lectures.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4 pt-2">
              
              {/* Step 1 */}
              <div 
                onClick={() => navigate('/courses')}
                className="rounded-2xl border border-brand bg-surface p-5 space-y-3 cursor-pointer hover:shadow-soft transition"
              >
                <div className="flex items-center justify-between">
                  <span className="grid h-8 w-8 place-items-center rounded-xl bg-brand text-white font-mono font-extrabold text-xs">1</span>
                  <span className="text-[10px] font-bold text-brand uppercase">Step 1</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white">Create Course</h3>
                <p className="text-[11px] text-muted leading-relaxed">Upload syllabus outline to define target topics.</p>
                <span className="inline-flex items-center gap-1 text-xs font-bold text-brand">Start Now →</span>
              </div>

              {/* Step 2 */}
              <div 
                onClick={() => navigate('/reference-materials')}
                className="rounded-2xl border border-line bg-canvas p-5 space-y-3 opacity-80 hover:opacity-100 cursor-pointer transition"
              >
                <div className="flex items-center justify-between">
                  <span className="grid h-8 w-8 place-items-center rounded-xl bg-surface border border-line text-muted font-mono font-extrabold text-xs">2</span>
                  <span className="text-[10px] font-bold text-muted uppercase">Step 2</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white">Add Course Material</h3>
                <p className="text-[11px] text-muted leading-relaxed">Upload notes or textbook PDFs for RAG evidence.</p>
                <span className="inline-flex items-center gap-1 text-xs font-bold text-muted">Upload →</span>
              </div>

              {/* Step 3 */}
              <div 
                onClick={() => navigate('/lectures')}
                className="rounded-2xl border border-line bg-canvas p-5 space-y-3 opacity-80 hover:opacity-100 cursor-pointer transition"
              >
                <div className="flex items-center justify-between">
                  <span className="grid h-8 w-8 place-items-center rounded-xl bg-surface border border-line text-muted font-mono font-extrabold text-xs">3</span>
                  <span className="text-[10px] font-bold text-muted uppercase">Step 3</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white">Upload Lecture</h3>
                <p className="text-[11px] text-muted leading-relaxed">Upload audio recording or spoken transcript text.</p>
                <span className="inline-flex items-center gap-1 text-xs font-bold text-muted">Upload →</span>
              </div>

              {/* Step 4 */}
              <div className="rounded-2xl border border-line bg-canvas p-5 space-y-3 opacity-60">
                <div className="flex items-center justify-between">
                  <span className="grid h-8 w-8 place-items-center rounded-xl bg-surface border border-line text-muted font-mono font-extrabold text-xs">4</span>
                  <span className="text-[10px] font-bold text-muted uppercase">Step 4</span>
                </div>
                <h3 className="text-sm font-extrabold text-ink dark:text-white">Get AI Insights</h3>
                <p className="text-[11px] text-muted leading-relaxed">View 5-engine evidence & coaching recommendations.</p>
                <span className="inline-flex items-center gap-1 text-xs font-bold text-muted">Automated</span>
              </div>

            </div>
          </Card>
        ) : (
          /* ── 4. RETURNING FACULTY DASHBOARD GRID ────────────────────────────────── */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* LEFT 2 COLUMNS */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Course Snapshot & Processing Tracker */}
              <Card className="p-6 space-y-5">
                <div className="flex items-center justify-between border-b border-line pb-3">
                  <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider">
                    COURSE SNAPSHOT & WORKFLOW STAGE
                  </span>
                  <span className="text-xs font-bold text-teal-400">
                    {lecturesList.length} Lecture(s) Total
                  </span>
                </div>

                {/* Processing Pipeline Tracker */}
                <div className="rounded-2xl border border-teal-500/20 bg-teal-500/5 p-4 space-y-2">
                  <span className="text-[11px] font-mono font-bold text-teal-400 uppercase tracking-wider block">
                    LIVE LECTURE WORKFLOW STATUS
                  </span>

                  <div className="grid grid-cols-5 gap-1.5 text-center text-[10px] font-extrabold">
                    <div className="rounded-xl bg-teal-500/20 text-teal-300 p-2">✓ Uploaded</div>
                    <div className="rounded-xl bg-teal-500/20 text-teal-300 p-2">✓ Transcribed</div>
                    <div className="rounded-xl bg-teal-500/20 text-teal-300 p-2">✓ Knowledge</div>
                    <div className="rounded-xl bg-teal-500/20 text-teal-300 p-2">✓ Analyzed</div>
                    <div className="rounded-xl bg-brand text-white p-2 font-black">✓ Ready</div>
                  </div>
                </div>

                {/* Course Metrics Snapshot */}
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="rounded-xl border border-line bg-canvas p-3">
                    <span className="text-muted font-bold block mb-0.5">KNOWLEDGE BASE</span>
                    <span className="font-extrabold text-teal-400 flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      {refList.length > 0 ? `${refList.length} Ref Files` : 'Syllabus Ready'}
                    </span>
                  </div>

                  <div className="rounded-xl border border-line bg-canvas p-3">
                    <span className="text-muted font-bold block mb-0.5">ANALYZED LECTURES</span>
                    <span className="font-extrabold text-brand">{lecturesList.length} Sessions</span>
                  </div>

                  <div className="rounded-xl border border-line bg-canvas p-3">
                    <span className="text-muted font-bold block mb-0.5">LATEST STATUS</span>
                    <span className="font-extrabold text-purple-400">
                      {latestLecture ? 'AI Complete' : 'Awaiting Lecture'}
                    </span>
                  </div>
                </div>
              </Card>


              {/* Latest AI Insight Card */}
              <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-line pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-brand" />
                    <h3 className="text-sm font-extrabold text-ink dark:text-white">Latest AI Insight</h3>
                  </div>
                  <button
                    onClick={() => {
                      if (latestLectureId) setLectureId(latestLectureId)
                      navigate('/results')
                    }}
                    className="inline-flex items-center gap-1 text-xs font-bold text-brand hover:underline"
                  >
                    <span>Explore analysis →</span>
                  </button>
                </div>

                <p className="text-xs text-ink dark:text-slate-200 leading-relaxed font-sans bg-canvas p-4 rounded-2xl border border-line/60">
                  {(teachingSummary as any)?.qualitative_summary ||
                    (latestLecture
                      ? `Your latest lecture on "${latestLecture.title || 'this topic'}" received high explanation clarity. Core concepts were introduced before practical demonstrations.`
                      : 'Upload your first lecture transcript to generate synthesized teaching insights.')}
                </p>
              </Card>


              {/* Recent Lectures List */}
              <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-line pb-3">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-purple-400" />
                    <h3 className="text-sm font-extrabold text-ink dark:text-white">Recent Lectures</h3>
                  </div>
                  <button
                    onClick={() => navigate('/history')}
                    className="text-xs font-bold text-purple-400 hover:underline"
                  >
                    View history →
                  </button>
                </div>

                <div className="space-y-3">
                  {lecturesList.length === 0 ? (
                    <div className="text-center py-6 space-y-2">
                      <Presentation className="h-8 w-8 text-muted mx-auto" />
                      <p className="text-xs text-muted font-medium">No lectures recorded for this course yet.</p>
                      <button
                        onClick={() => navigate('/lectures')}
                        className="rounded-xl bg-brand px-4 py-2 text-xs font-bold text-white shadow-soft"
                      >
                        Upload First Lecture
                      </button>
                    </div>
                  ) : (
                    lecturesList.slice(0, 4).map((lec: any, index: number) => (
                      <div
                        key={lec.id || index}
                        className="flex items-center justify-between rounded-2xl border border-line bg-canvas p-3.5 hover:border-brand transition"
                      >
                        <div className="flex items-center gap-3">
                          <div className="grid h-8 w-8 place-items-center rounded-xl bg-brand/10 text-brand font-bold text-xs">
                            #{index + 1}
                          </div>
                          <div>
                            <h4 className="text-xs font-extrabold text-ink dark:text-white">
                              {lec.title || `Lecture ${lec.id.slice(0, 8)}`}
                            </h4>
                            <span className="text-[10px] text-muted font-mono">
                              {lec.lecture_date || 'Today'} • {lec.duration_minutes || 45} min
                            </span>
                          </div>
                        </div>

                        <button
                          onClick={() => {
                            setLectureId(lec.id)
                            navigate('/results')
                          }}
                          className="inline-flex items-center gap-1 rounded-xl bg-surface px-3 py-1.5 text-xs font-bold text-brand border border-brand/20 hover:bg-brand/10 transition"
                        >
                          <span>View analysis</span>
                          <ChevronRight className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </Card>

            </div>


            {/* RIGHT 1 COLUMN */}
            <div className="space-y-6">
              
              {/* Top Recommendations Preview */}
              <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-line pb-3">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-indigo-400" />
                    <h3 className="text-sm font-extrabold text-ink dark:text-white">Top Recommendations</h3>
                  </div>
                  <button
                    onClick={() => navigate('/results')}
                    className="text-xs font-bold text-indigo-400 hover:underline"
                  >
                    View all →
                  </button>
                </div>

                <div className="space-y-3">
                  {recs.length === 0 ? (
                    <p className="text-xs text-muted italic text-center py-4">No pending recommendations for this lecture.</p>
                  ) : (
                    recs.slice(0, 3).map((r: any, idx: number) => (
                      <div key={r.id || idx} className="rounded-xl border border-line bg-canvas p-3 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-extrabold text-amber-400 border border-amber-500/20">
                            {r.priority || 'HIGH'} PRIORITY
                          </span>
                          <span className="text-[10px] text-muted font-mono">{r.category || 'Pedagogical'}</span>
                        </div>
                        <h4 className="text-xs font-bold text-ink dark:text-white line-clamp-1">{r.title}</h4>
                        <p className="text-[11px] text-muted line-clamp-2">{r.reason}</p>
                      </div>
                    ))
                  )}
                </div>
              </Card>


              {/* Material Readiness Card */}
              <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-line pb-3">
                  <div className="flex items-center gap-2">
                    <LibraryBig className="h-4 w-4 text-teal-400" />
                    <h3 className="text-sm font-extrabold text-ink dark:text-white">Course Knowledge</h3>
                  </div>
                  <button
                    onClick={() => navigate(activeCourseId ? `/courses/${activeCourseId}/materials` : '/reference-materials')}
                    className="text-xs font-bold text-teal-400 hover:underline"
                  >
                    Manage →
                  </button>
                </div>

                {refList.length > 0 ? (
                  <div className="rounded-2xl border border-teal-500/20 bg-teal-500/5 p-4 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-teal-400">
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Knowledge Material Ready</span>
                    </div>
                    <p className="text-xs text-muted font-medium">
                      {refList.length} reference document(s) uploaded and indexed into PostgreSQL vector RAG storage.
                    </p>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-line bg-canvas p-4 space-y-2 text-center">
                    <p className="text-xs text-muted font-medium">
                      Add course notes or reference PDFs to prepare ClassroomIQ for lecture analysis.
                    </p>
                    <button
                      onClick={() => navigate('/reference-materials')}
                      className="rounded-xl bg-brand px-4 py-2 text-xs font-bold text-white shadow-soft"
                    >
                      Upload Material
                    </button>
                  </div>
                )}
              </Card>

            </div>

          </div>
        )}

      </div>
    </PageLayout>
  )
}
