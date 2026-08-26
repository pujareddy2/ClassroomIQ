import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, BookOpen, Upload, ArrowRight, Loader2, X, Trash2, Eye } from 'lucide-react'
import { PageLayout } from '@/components/page-layout'
import { Card, EmptyState } from '@/components/ui'
import { curriculumService } from '@/services/curriculum-service'
import { useContextStore } from '@/store/context-store'
import { useAuthStore } from '@/store/auth-store'
import { friendlyError } from '@/hooks/use-api-query'

export function CoursesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const { setCourseId, setCurriculumId, setSemester } = useContextStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [deletingCurriculumId, setDeletingCurriculumId] = useState<string | null>(null)
  const [courseName, setCourseName] = useState('')
  const [semester, setSemesterInput] = useState('Fall 2026')
  const [academicYear, setAcademicYear] = useState('2026-2027')
  const [syllabusFile, setSyllabusFile] = useState<File | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  // Fetch all curricula / courses
  const { data: rawCurricula, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['curricula'],
    queryFn: curriculumService.list
  })

  // Create course mutation
  const createCourseMutation = useMutation({
    mutationFn: curriculumService.upload,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['curricula'] })
      const courseId = String(data.course_id || 'crs_' + Date.now())
      const curriculumId = String(data.id || data.document_id || '')
      
      setCourseId(courseId, courseName.trim())
      setCurriculumId(curriculumId)
      setSemester(semester)

      setIsModalOpen(false)
      navigate(`/courses/${courseId}/materials`)
    }
  })

  // Delete course mutation
  const deleteCourseMutation = useMutation({
    mutationFn: curriculumService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['curricula'] })
      setDeletingCurriculumId(null)
    }
  })

  const handleCreateCourse = (e: React.FormEvent) => {
    e.preventDefault()
    if (!courseName.trim()) {
      setFormError('Course Name is required.')
      return
    }
    if (!syllabusFile) {
      setFormError('Please select a course syllabus or outline document.')
      return
    }

    setFormError(null)

    const formData = new FormData()
    formData.append('course_name', courseName.trim())
    formData.append('academic_year', '2026-2027')
    formData.append('semester', '6')
    formData.append('faculty_name', user?.full_name || 'Faculty Member')
    formData.append('title', `${courseName.trim()} Syllabus`)
    formData.append('document_type', 'SYLLABUS')
    formData.append('file', syllabusFile)

    createCourseMutation.mutate(formData)
  }

  // Deduplicate curricula by course_id/course_name
  const coursesList = rawCurricula ? [...new Map(rawCurricula.map(item => {
    const rec = item as Record<string, unknown>
    return [String(rec.course_id || rec.course_name), rec]
  })).values()] : []

  return (
    <PageLayout
      title="Your Courses"
      description="Set up and manage your academic courses. ClassroomIQ uses course materials to build lecture intelligence."
      hideContextBadges={true}
      actions={
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-5 text-sm font-bold text-white shadow-soft transition hover:bg-brand/90 hover:scale-105 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          <span>Create Course</span>
        </button>
      }
    >
      {/* Course List Grid */}
      {isLoading ? (
        <div className="grid min-h-[300px] place-items-center rounded-3xl border border-line bg-surface p-8 text-center text-sm font-semibold text-muted">
          Loading your courses…
        </div>
      ) : isError ? (
        <div className="rounded-3xl border border-danger/20 bg-danger/10 p-6 text-center text-xs font-semibold text-danger">
          Failed to load courses. <button onClick={() => refetch()} className="underline font-bold">Retry</button>
        </div>
      ) : coursesList.length === 0 ? (
        <EmptyState
          title="No courses created yet"
          description="Create a course and upload your syllabus or notes so ClassroomIQ can prepare its knowledge base before analyzing your lectures."
          action={
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-6 text-sm font-bold text-white shadow-soft hover:bg-brand/90"
            >
              <Plus className="h-4 w-4" />
              <span>Create Your First Course</span>
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {coursesList.map((item) => {
            const course = item as Record<string, unknown>
            const courseId = String(course.course_id || course.id)
            const curriculumId = String(course.id || course.document_id || courseId)
            const cName = String(course.course_name || course.title || 'Untitled Course')
            const cSem = String(course.semester || 'Fall 2026')
            const cYear = String(course.academic_year || '2026-2027')
            const fName = String(course.faculty_name || user?.full_name || 'Faculty')

            return (
              <Card
                key={courseId}
                className="group relative flex flex-col justify-between p-6 transition-all duration-300 hover:border-brand/40 hover:-translate-y-1 shadow-soft"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-soft text-brand">
                      <BookOpen className="h-5 w-5" />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono font-bold text-teal-400 bg-teal-500/10 px-2.5 py-0.5 rounded-full border border-teal-400/20">
                        ✓ Active Course
                      </span>
                      <button
                        onClick={() => setDeletingCurriculumId(curriculumId)}
                        className="p-1.5 rounded-lg border border-line bg-canvas text-muted hover:text-danger hover:border-danger/30 transition"
                        title="Delete course"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-extrabold text-ink dark:text-white group-hover:text-brand transition leading-tight">
                      {cName}
                    </h3>
                    <p className="mt-1 text-xs font-semibold text-muted dark:text-slate-300">
                      {cSem} · {cYear}
                    </p>
                  </div>

                  <div className="pt-2 text-xs font-medium text-slate-300 space-y-1">
                    <p><span className="text-muted dark:text-slate-400 font-bold">Faculty:</span> {fName}</p>
                    <p><span className="text-muted dark:text-slate-400 font-bold">Knowledge Base:</span> Ready for lecture analysis</p>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-line flex items-center justify-between">
                  <button
                    onClick={() => {
                      setCourseId(courseId, cName)
                      setCurriculumId(curriculumId)
                      setSemester(cSem)
                      navigate(`/courses/${courseId}/materials`)
                    }}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-brand hover:underline"
                  >
                    <span>Open Course Materials</span>
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </button>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* DELETE COURSE CONFIRMATION MODAL */}
      {deletingCurriculumId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="relative w-full max-w-sm rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 shadow-2xl text-ink dark:text-white space-y-4 text-center">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-danger/10 text-danger mx-auto">
              <Trash2 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-extrabold text-ink dark:text-white">Delete this course?</h3>
            <p className="text-xs text-muted dark:text-slate-300 font-bold leading-relaxed">
              This course and its syllabus knowledge base will be removed from your workspace.
            </p>

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setDeletingCurriculumId(null)}
                className="h-10 rounded-xl border border-line bg-canvas px-5 text-xs font-bold text-muted hover:text-ink"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteCourseMutation.mutate(deletingCurriculumId)}
                disabled={deleteCourseMutation.isPending}
                className="h-10 rounded-xl bg-danger px-6 text-xs font-bold text-white shadow-soft hover:bg-danger/90 disabled:opacity-60"
              >
                {deleteCourseMutation.isPending ? 'Deleting…' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE COURSE MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
          <div className="relative w-full max-w-md rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-8 shadow-2xl text-ink dark:text-white space-y-6">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div>
                <span className="text-xs font-mono font-bold text-brand uppercase">ACADEMIC KNOWLEDGE SETUP</span>
                <h2 className="text-xl font-extrabold text-ink dark:text-white">Create a course</h2>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded-xl border border-line p-2 text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-xs text-muted dark:text-slate-300 font-bold leading-relaxed">
              Set up the course you want ClassroomIQ to understand.
            </p>

            <form onSubmit={handleCreateCourse} className="space-y-4">
              {/* Course Name */}
              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                  Course Name <span className="text-danger">*</span>
                </label>
                <input
                  required
                  value={courseName}
                  onChange={(e) => setCourseName(e.target.value)}
                  placeholder="e.g. Data Structures & Algorithms"
                  className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                />
              </div>

              {/* Semester & Academic Year */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    Semester <span className="text-danger">*</span>
                  </label>
                  <input
                    required
                    value={semester}
                    onChange={(e) => setSemesterInput(e.target.value)}
                    placeholder="e.g. Fall 2026"
                    className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    Academic Year <span className="text-danger">*</span>
                  </label>
                  <input
                    required
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                    placeholder="e.g. 2026-2027"
                    className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                  />
                </div>
              </div>

              {/* Syllabus File Upload */}
              <div>
                <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                  Course Syllabus / Outline Document <span className="text-danger">*</span>
                </label>
                <div className="rounded-2xl border border-dashed border-line bg-canvas p-4 text-center">
                  <input
                    required
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={(e) => setSyllabusFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="syllabus-file-input"
                  />
                  <label htmlFor="syllabus-file-input" className="cursor-pointer space-y-2 block">
                    <Upload className="h-6 w-6 text-brand mx-auto" />
                    {syllabusFile ? (
                      <span className="text-xs font-bold text-teal-400 block truncate">
                        ✓ {syllabusFile.name} ({(syllabusFile.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    ) : (
                      <span className="text-xs font-bold text-muted dark:text-slate-300 block">
                        Click to select Syllabus PDF, DOCX, or TXT
                      </span>
                    )}
                  </label>
                </div>
              </div>

              {/* Errors */}
              {(formError || createCourseMutation.error) && (
                <div className="rounded-xl border border-danger/20 bg-danger/10 p-3 text-xs font-bold text-danger">
                  {formError || friendlyError(createCourseMutation.error)}
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3 border-t border-line">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="h-11 rounded-xl border border-line bg-canvas px-5 text-xs font-bold text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createCourseMutation.isPending}
                  className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-6 text-xs font-bold text-white shadow-soft hover:bg-brand/90 disabled:opacity-60 transition"
                >
                  {createCourseMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Creating Course…</span>
                    </>
                  ) : (
                    <span>Create Course</span>
                  )}
                </button>
              </div>

            </form>

          </div>
        </div>
      )}
    </PageLayout>
  )
}
