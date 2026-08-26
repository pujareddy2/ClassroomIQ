import { useApiQuery } from '@/hooks/use-api-query'
import { useQueries } from '@tanstack/react-query'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { PageLayout } from '@/components/page-layout'
import { AnalysisProgress, ErrorState, LectureRequired, LoadingState } from '@/components/page-state'
import { Card, EmptyState } from '@/components/ui'
import { curriculumService } from '@/services/curriculum-service'
import { lectureService } from '@/services/lecture-service'
import { referenceService } from '@/services/reference-service'
import { coverageService, explainabilityService, recommendationService, teachingService, validationService } from '@/services/intelligence-services'
import { analyticsService } from '@/services/analytics-service'
import { reportService } from '@/services/report-service'
import { authService } from '@/services/auth-service'
import { useContextStore } from '@/store/context-store'
import { useUiStore } from '@/store/ui-store'
import { useAuthStore } from '@/store/auth-store'
import { WorkflowStatus } from '@/components/workflow-status'
import { useLectureAnalysis } from '@/hooks/use-analysis-workflow'

const label = (key: string) => key.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
const publicEntries = (record: Record<string, unknown>) => Object.entries(record).filter(([key, entry]) => !/(^id$|_id$|path|raw|extracted)/i.test(key) && (typeof entry !== 'object' || entry === null))
function DataCard({ title, value }: { title: string; value: unknown }) { const entries = value && typeof value === 'object' && !Array.isArray(value) ? publicEntries(value as Record<string, unknown>) : []; return <Card><h2 className="text-sm font-semibold">{title}</h2>{Array.isArray(value) ? value.length ? <div className="mt-4 space-y-2">{value.slice(0, 20).map((item, index) => <div key={index} className="rounded-xl bg-elevated p-3 text-sm text-muted">{typeof item === 'object' ? publicEntries(item as Record<string, unknown>).slice(0, 4).map(([key, entry]) => <p key={key}><span className="font-medium text-ink">{label(key)}: </span>{String(entry ?? '—')}</p>) : String(item)}</div>)}</div> : <p className="mt-4 text-sm text-muted">No records were returned.</p> : entries.length ? <dl className="mt-4 grid gap-3 sm:grid-cols-2">{entries.map(([key, entry]) => <div key={key} className="rounded-xl bg-elevated p-3"><dt className="text-xs text-muted">{label(key)}</dt><dd className="mt-1 break-words text-sm font-semibold">{String(entry ?? '—')}</dd></div>)}</dl> : <p className="mt-4 text-sm text-muted">No teacher-facing details are available.</p>}</Card> }
type IntelligenceQuery = { title: string; key: string; fn: (id: string) => Promise<unknown> }
function QueryPageBody({ queries }: { queries: IntelligenceQuery[] }) { const lectureId = useContextStore((s) => s.selectedLectureId); const curriculumId = useContextStore((s) => s.selectedCurriculumId); const analysis = useLectureAnalysis(); const queryResults = useQueries({ queries: queries.map((item) => ({ queryKey: [item.key, lectureId], queryFn: () => item.fn(lectureId!), enabled: Boolean(lectureId && curriculumId && analysis.isCompleted), retry: false })) }); const results = queries.map((item, index) => ({ ...item, query: queryResults[index] })); const stage = analysis.status?.current_stage; const progressLabel = stage && !['QUEUED', 'NOT_STARTED'].includes(stage) ? `Generating ${stage === 'TEACHING' ? 'Teaching Analysis' : stage[0] + stage.slice(1).toLowerCase()} (${analysis.status?.progress_percentage ?? 0}%)...` : 'Checking existing analysis...'; return !lectureId ? <LectureRequired/> : !curriculumId ? <EmptyState title="Select a curriculum first" description="Coverage and all downstream analysis require the curriculum linked to this lecture."/> : analysis.isChecking || (!analysis.isCompleted && !analysis.isFailed && !analysis.timedOut) ? <AnalysisProgress label={progressLabel}/> : analysis.timedOut ? <ErrorState error={new Error('Analysis is taking longer than expected. You can retry or refresh its status.')} retry={analysis.retry}/> : analysis.isFailed ? <ErrorState error={analysis.error ?? new Error(analysis.status?.error_message ?? 'Analysis failed.')} retry={analysis.retry}/> : results.some((r) => r.query.isLoading) ? <LoadingState/> : results.find((r) => r.query.isError) ? <ErrorState error={results.find((r) => r.query.error)?.query.error} retry={() => results.forEach((r) => r.query.refetch())}/> : <div className="grid gap-4 xl:grid-cols-2">{results.map((r) => <DataCard key={r.key} title={r.title} value={r.query.data}/>)}</div> }
function QueryPage({ title, description, queries }: { title: string; description: string; queries: IntelligenceQuery[] }) { return <PageLayout title={title} description={description}><QueryPageBody queries={queries}/></PageLayout> }

export { DashboardPage } from './dashboard-page'
export { HistoryPage } from './history-page'
export function CoveragePage() { return <QueryPage title="Coverage" description="Live curriculum coverage, topic outcomes, remaining curriculum, and timeline." queries={[{ title: 'Coverage summary', key: 'coverage-summary', fn: coverageService.summary }, { title: 'Topic coverage', key: 'coverage-topics', fn: coverageService.topics }, { title: 'Remaining curriculum', key: 'coverage-remaining', fn: coverageService.remaining }, { title: 'Coverage timeline', key: 'coverage-timeline', fn: coverageService.timeline }]}/> }
export function ValidationPage() { return <QueryPage title="Technical Validation" description="Evidence-backed validation results from the selected lecture." queries={[{ title: 'Validation summary', key: 'validation-summary', fn: validationService.summary }, { title: 'Validation results', key: 'validation-results', fn: validationService.results }, { title: 'Evidence', key: 'validation-evidence', fn: validationService.evidence }, { title: 'Timeline', key: 'validation-timeline', fn: validationService.timeline }]}/> }
export function TeachingPage() { return <QueryPage title="Teaching Intelligence" description="Teaching quality, strengths, weaknesses, examples, interaction, and structure." queries={[{ title: 'Teaching summary', key: 'teaching-summary', fn: teachingService.summary }, { title: 'Strengths', key: 'teaching-strengths', fn: teachingService.strengths }, { title: 'Weaknesses', key: 'teaching-weaknesses', fn: teachingService.weaknesses }, { title: 'Interaction', key: 'teaching-interaction', fn: teachingService.interaction }, { title: 'Structure', key: 'teaching-structure', fn: teachingService.structure }]}/> }
export function RecommendationsPage() { return <QueryPage title="Recommendations" description="Prioritized coaching actions and their supporting evidence." queries={[{ title: 'Recommendations', key: 'recommendations', fn: recommendationService.list }, { title: 'Priority breakdown', key: 'recommendation-priority', fn: recommendationService.priority }, { title: 'Evidence', key: 'recommendation-evidence', fn: recommendationService.evidence }]}/> }
export function ExplainabilityPage() { return <QueryPage title="Explainable AI" description="Decision context, evidence, citations, confidence, and reasoning for the selected lecture." queries={[{ title: 'Explanation package', key: 'explanation-package', fn: explainabilityService.package }, { title: 'Summary', key: 'explanation-summary', fn: explainabilityService.summary }, { title: 'Evidence', key: 'explanation-evidence', fn: explainabilityService.evidence }, { title: 'Transcript evidence', key: 'explanation-transcripts', fn: explainabilityService.transcripts }, { title: 'Citations', key: 'explanation-citations', fn: explainabilityService.citations }, { title: 'Confidence', key: 'explanation-confidence', fn: explainabilityService.confidence }, { title: 'Reasoning', key: 'explanation-reasoning', fn: explainabilityService.reasoning }]}/> }
function UploadCard({ title, onSubmit, pending, children }: { title: string; onSubmit: (data: FormData) => void; pending: boolean; children: React.ReactNode }) { return <Card><h2 className="font-semibold">{title}</h2><form className="mt-4 grid gap-3 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); onSubmit(new FormData(event.currentTarget)) }}>{children}<button disabled={pending} className="min-h-10 rounded-xl bg-brand px-4 text-sm font-semibold text-white disabled:opacity-60 sm:col-span-2">{pending ? 'Uploading…' : title}</button></form></Card> }
const Input = ({ name, label: text, required = true, type = 'text' }: { name: string; label: string; required?: boolean; type?: string }) => <label className="text-sm font-medium">{text}<input required={required} type={type} name={name} className="mt-1.5 h-10 w-full rounded-xl border border-line bg-canvas px-3 text-sm outline-none"/></label>
export function CurriculumPage() { const queryClient = useQueryClient(); const addNotification = useUiStore((state) => state.addNotification); const { setCurriculumId, setCourseId, setSemester } = useContextStore(); const [notice, setNotice] = useState<string | null>(null); const upload = useMutation({ mutationFn: curriculumService.upload, onSuccess: (data) => { const record = data as { document_id?: string; course_id?: string; academic_year?: string; semester?: string }; setCurriculumId(record.document_id ?? null); setCourseId(record.course_id ?? null); setSemester(record.semester ?? record.academic_year ?? null); setNotice('Curriculum uploaded and selected.'); addNotification({ id: crypto.randomUUID(), title: 'Curriculum uploaded', body: 'Your curriculum is ready to use.', category: 'System', priority: 'info', createdAt: new Date().toISOString(), read: false }); queryClient.invalidateQueries({ queryKey: ['curricula'] }) } }); const query = useApiQuery(['curricula'], curriculumService.list); return <PageLayout title="Curriculum" description="Upload and select the curriculum that guides your lecture intelligence.">{notice && <p className="rounded-xl bg-success/10 p-3 text-sm text-success">{notice}</p>}<UploadCard title="Upload curriculum" pending={upload.isPending} onSubmit={upload.mutate}><Input name="course_name" label="Course name"/><Input name="academic_year" label="Academic year"/><Input name="semester" label="Semester"/><Input name="faculty_name" label="Faculty name"/><Input name="title" label="Curriculum title"/><label className="text-sm font-medium">Document type<select name="document_type" defaultValue="SYLLABUS" className="mt-1.5 h-10 w-full rounded-xl border border-line bg-canvas px-3 text-sm"><option value="SYLLABUS">Syllabus</option></select></label><label className="text-sm font-medium sm:col-span-2">Syllabus file<input required name="file" type="file" accept=".pdf,.docx,.txt" className="mt-1.5 block w-full text-sm"/></label></UploadCard>{query.isLoading ? <LoadingState/> : query.isError ? <ErrorState error={query.error} retry={() => query.refetch()}/> : !query.data?.length ? <EmptyState title="No curricula found" description="Upload a syllabus to create your active curriculum."/> : <div className="grid gap-4 md:grid-cols-2">{query.data.map((item, index) => <button key={index} onClick={() => { const record = item as Record<string, unknown>; setCurriculumId(String(record.id)); setCourseId(String(record.course_id)); setSemester(null); setNotice('Active curriculum updated.'); }} className="text-left"><DataCard title="Select curriculum" value={item}/></button>)}</div>}</PageLayout> }
export function ReferenceMaterialsPage() {
  const queryClient = useQueryClient();
  const addNotification = useUiStore((state) => state.addNotification);
  const selectedCourseId = useContextStore((state) => state.selectedCourseId);
  const [notice, setNotice] = useState<string | null>(null);
  const reference = useMutation({
    mutationFn: referenceService.upload,
    onSuccess: () => {
      setNotice('Reference material uploaded and RAG indexed successfully.');
      addNotification({
        id: crypto.randomUUID(),
        title: 'Reference material uploaded',
        body: 'Your reference material is ready for RAG evidence retrieval.',
        category: 'Validation',
        priority: 'info',
        createdAt: new Date().toISOString(),
        read: false,
      });
      queryClient.invalidateQueries({ queryKey: ['reference-materials'] });
    },
  });

  const query = useApiQuery(
    ['reference-materials', selectedCourseId],
    () => referenceService.list(selectedCourseId ?? undefined),
    Boolean(selectedCourseId)
  );

  return (
    <PageLayout
      title="Reference Materials"
      description="Upload approved source material used by ClassroomIQ RAG retrieval and technical validation."
    >
      {notice && <p className="rounded-xl bg-success/10 p-3 text-sm text-success">{notice}</p>}
      <UploadCard title="Upload reference material" pending={reference.isPending} onSubmit={reference.mutate}>
        <Input name="course_name" label="Course name" />
        <Input name="academic_year" label="Academic year" />
        <Input name="semester" label="Semester" />
        <Input name="faculty_name" label="Faculty name" />
        <Input name="title" label="Reference title" />
        <label className="text-sm font-medium">
          Document type
          <select name="document_type" defaultValue="FACULTY_NOTES" className="mt-1.5 h-10 w-full rounded-xl border border-line bg-canvas px-3 text-sm">
            <option value="REFERENCE_BOOK">Reference book</option>
            <option value="FACULTY_NOTES">Faculty notes</option>
            <option value="PPT">Presentation</option>
            <option value="LAB_MANUAL">Lab manual</option>
            <option value="ASSIGNMENT">Assignment</option>
            <option value="QUESTION_BANK">Question bank</option>
          </select>
        </label>
        <label className="text-sm font-medium sm:col-span-2">
          Reference file
          <input required name="file" type="file" accept=".pdf,.docx,.txt,.ppt,.pptx" className="mt-1.5 block w-full text-sm" />
        </label>
      </UploadCard>

      {query.isLoading ? (
        <LoadingState />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => query.refetch()} />
      ) : !query.data?.length ? (
        <EmptyState
          title="No reference materials found"
          description="Upload a reference book or notes file to index it for academic evidence retrieval."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {query.data.map((item, index) => (
            <DataCard key={index} title="Reference Material" value={item} />
          ))}
        </div>
      )}
    </PageLayout>
  );
}
function UnavailablePage({ title, kind }: { title: string; kind: 'analytics' | 'reports' }) { const service = kind === 'analytics' ? analyticsService : reportService; const query = useApiQuery([kind, 'availability'], service.unavailable, false); return <PageLayout title={title} description="This view will connect as soon as its backend router is available."><EmptyState title={`${title} API is not available`} description="The current FastAPI route inventory has no corresponding endpoint. No data has been fabricated; add the backend router and this page can be connected through its dedicated service."/></PageLayout> }
export const AnalyticsPage = () => <UnavailablePage title="Analytics" kind="analytics"/>
export const ReportsPage = () => <UnavailablePage title="Reports" kind="reports"/>
export const ProfilePage = () => <PageLayout title="Faculty Profile" description="Manage your academic identity, institutional affiliation, and faculty credentials." hideContextBadges={true}><ProfileContent/></PageLayout>
function ProfileContent() {
  const { user, updateUserProfile } = useAuthStore()
  const [isEditing, setIsEditing] = useState(false)
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [institution, setInstitution] = useState(user?.institution || '')
  const [department, setDepartment] = useState(user?.department || '')
  const [designation, setDesignation] = useState(user?.designation || 'Faculty')
  const [profileImage, setProfileImage] = useState(user?.profileImage || '')

  const getInitials = (name?: string) => {
    if (!name) return 'IQ'
    const parts = name.trim().split(' ')
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    }
    return name.slice(0, 2).toUpperCase()
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setProfileImage(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    updateUserProfile({
      full_name: fullName.trim(),
      institution: institution.trim(),
      department: department.trim(),
      designation,
      profileImage: profileImage || undefined
    })
    setIsEditing(false)
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Avatar Header */}
      <Card className="relative overflow-hidden p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
          {/* Avatar */}
          {user?.profileImage || profileImage ? (
            <img
              src={profileImage || user?.profileImage}
              alt={user?.full_name || 'Faculty Avatar'}
              className="h-24 w-24 rounded-2xl object-cover border-2 border-brand shadow-soft shrink-0"
            />
          ) : (
            <div className="grid h-24 w-24 place-items-center rounded-2xl bg-gradient-to-br from-brand via-indigo-500 to-purple-600 text-2xl font-extrabold text-white shadow-soft shrink-0">
              {getInitials(user?.full_name)}
            </div>
          )}

          {/* User Details Header */}
          <div className="flex-1 text-center sm:text-left space-y-2">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
              <h2 className="text-2xl font-extrabold text-ink dark:text-white">{user?.full_name || 'Faculty Member'}</h2>
              <span className="inline-flex items-center gap-1 rounded-full bg-teal-500/10 px-3 py-0.5 text-xs font-bold text-teal-400 border border-teal-400/20">
                ✓ Profile Setup Complete
              </span>
            </div>

            <p className="text-sm font-semibold text-muted dark:text-slate-300">
              {user?.designation || 'Faculty'} · {user?.department || 'Department Not Specified'}
            </p>
            <p className="text-xs font-mono text-brand font-bold">
              {user?.institution || 'Institution Not Specified'}
            </p>
          </div>

          {/* Edit Action Button */}
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-canvas px-4 text-xs font-bold text-ink dark:text-white hover:bg-surface transition shadow-soft shrink-0"
          >
            <span>{isEditing ? 'Cancel Edit' : 'Edit Profile'}</span>
          </button>
        </div>
      </Card>

      {/* Edit Form OR View Details Grid */}
      {isEditing ? (
        <Card className="p-6 sm:p-8 space-y-6">
          <h3 className="text-lg font-bold text-ink dark:text-white border-b border-line pb-3">Update Faculty Profile</h3>
          <form onSubmit={handleSave} className="space-y-4">
            {/* Avatar Photo Upload */}
            <div>
              <label className="block text-xs font-bold text-ink dark:text-white mb-1">Profile Photo</label>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="block w-full text-xs text-muted font-medium border border-line bg-canvas p-2.5 rounded-xl cursor-pointer"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">Full Name</label>
                <input
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">Institution / University</label>
                <input
                  required
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                  className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">Department</label>
                <input
                  required
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">Designation</label>
                <select
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                  className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-bold text-ink dark:text-white outline-none focus:border-brand"
                >
                  <option value="Professor">Professor</option>
                  <option value="Associate Professor">Associate Professor</option>
                  <option value="Assistant Professor">Assistant Professor</option>
                  <option value="Lecturer">Lecturer</option>
                  <option value="Faculty">Faculty Member</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="h-10 rounded-xl border border-line bg-canvas px-4 text-xs font-bold text-muted hover:text-ink"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="h-10 rounded-xl bg-brand px-6 text-xs font-bold text-white shadow-soft hover:bg-brand/90"
              >
                Save Profile
              </button>
            </div>
          </form>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-2xl border border-line bg-surface p-5 space-y-1">
            <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase block">Full Name</span>
            <p className="text-base font-bold text-ink dark:text-white">{user?.full_name || '—'}</p>
          </div>

          <div className="rounded-2xl border border-line bg-surface p-5 space-y-1">
            <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase block">Email Address</span>
            <p className="text-base font-bold text-ink dark:text-white">{user?.email || '—'}</p>
          </div>

          <div className="rounded-2xl border border-line bg-surface p-5 space-y-1">
            <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase block">Institution / University</span>
            <p className="text-base font-bold text-ink dark:text-white">{user?.institution || '—'}</p>
          </div>

          <div className="rounded-2xl border border-line bg-surface p-5 space-y-1">
            <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase block">Department</span>
            <p className="text-base font-bold text-ink dark:text-white">{user?.department || '—'}</p>
          </div>

          <div className="rounded-2xl border border-line bg-surface p-5 space-y-1">
            <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase block">Designation</span>
            <p className="text-base font-bold text-ink dark:text-white">{user?.designation || '—'}</p>
          </div>

          <div className="rounded-2xl border border-line bg-surface p-5 space-y-1">
            <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase block">Academic Role</span>
            <p className="text-base font-bold text-ink dark:text-white capitalize">{user?.role || 'Faculty'}</p>
          </div>
        </div>
      )}
    </div>
  )
}
export const SettingsPage = () => <PageLayout title="Settings" description="Workspace preferences are persisted locally and applied across the application."><Card><p className="text-sm text-muted">Theme, sidebar state, selected lecture, course, and semester are saved in your browser. Server-backed preferences require a settings API endpoint.</p></Card></PageLayout>
export const SupportPage = () => <PageLayout title="Support" description="Get help with ClassroomIQ."><EmptyState title="Need assistance?" description="Contact your ClassroomIQ administrator or support team."/></PageLayout>
