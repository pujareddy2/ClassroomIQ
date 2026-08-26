import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Presentation, 
  Search, 
  Filter, 
  Clock, 
  FileText, 
  Sparkles, 
  Trash2, 
  Eye, 
  CheckCircle2, 
  AlertTriangle,
  FolderKanban,
  Calendar
} from 'lucide-react'
import { PageLayout } from '@/components/page-layout'
import { Card, EmptyState } from '@/components/ui'
import { useContextStore } from '@/store/context-store'
import { lectureService } from '@/services/lecture-service'
import { curriculumService } from '@/services/curriculum-service'

export function HistoryPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const { selectedCourseId, selectedCourseName, setLectureId, setCourseId } = useContextStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'READY' | 'PROCESSING' | 'FAILED'>('ALL')
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Fetch curricula list for course filter
  const { data: rawCurricula } = useQuery({
    queryKey: ['curricula'],
    queryFn: curriculumService.list
  })

  const coursesList = useMemo(() => {
    if (!rawCurricula) return []
    const map = new Map<string, Record<string, any>>()
    rawCurricula.forEach((item) => {
      const rec = item as Record<string, any>
      const cId = String(rec.course_id || rec.id || '')
      const cName = String(rec.course_name || rec.title || 'Course')
      if (cId && (!map.has(cId) || rec.document_type === 'SYLLABUS')) {
        map.set(cId, { id: cId, name: cName })
      }
    })
    return Array.from(map.values())
  }, [rawCurricula])

  // Fetch lectures (scoped to selected course if specified, or all)
  const { data: rawLectures, isLoading, refetch } = useQuery({
    queryKey: ['history-lectures', selectedCourseId],
    queryFn: () => lectureService.list(selectedCourseId || undefined)
  })

  // Delete lecture mutation
  const deleteMutation = useMutation({
    mutationFn: lectureService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history-lectures'] })
      queryClient.invalidateQueries({ queryKey: ['lectures'] })
      setDeletingId(null)
    }
  })

  const lecturesList = (rawLectures as Array<Record<string, any>>) || []

  // Filter lectures
  const filteredLectures = useMemo(() => {
    return lecturesList.filter((lec) => {
      const title = String(lec.title || '').toLowerCase()
      const status = String(lec.status || 'COMPLETED').toUpperCase()
      
      const matchesSearch = title.includes(searchQuery.toLowerCase())
      if (!matchesSearch) return false

      if (statusFilter === 'READY') return status === 'READY' || status === 'COMPLETED'
      if (statusFilter === 'PROCESSING') return status === 'PROCESSING' || status === 'PENDING'
      if (statusFilter === 'FAILED') return status === 'FAILED'

      return true
    })
  }, [lecturesList, searchQuery, statusFilter])

  return (
    <PageLayout
      title="Lecture History"
      description="Review past lecture sessions, view historical AI analysis, and track academic progress across your courses."
    >
      <div className="space-y-6">
        
        {/* Filter Bar */}
        <Card className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border border-line">
          <div className="flex flex-wrap items-center gap-3">
            
            {/* Search Input */}
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search lectures..."
                className="h-10 w-full rounded-xl border border-line bg-canvas pl-9 pr-3 text-xs font-medium text-ink dark:text-white outline-none focus:border-brand"
              />
            </div>

            {/* Course Filter */}
            {coursesList.length > 0 && (
              <div className="flex items-center gap-2 rounded-xl bg-canvas p-1 border border-line">
                <FolderKanban className="h-4 w-4 text-brand ml-2" />
                <select
                  value={selectedCourseId || ''}
                  onChange={(e) => {
                    const found = coursesList.find((c) => c.id === e.target.value)
                    setCourseId(e.target.value || null, found?.name)
                  }}
                  className="h-8 bg-transparent text-xs font-bold text-ink dark:text-white outline-none cursor-pointer pr-3"
                >
                  <option value="" className="bg-surface text-ink">All Courses</option>
                  {coursesList.map((c) => (
                    <option key={c.id} value={c.id} className="bg-surface text-ink">
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Status Filter Pills */}
            <div className="flex rounded-xl bg-canvas p-1 border border-line text-xs font-bold">
              <button
                onClick={() => setStatusFilter('ALL')}
                className={`px-3 py-1.5 rounded-lg transition ${statusFilter === 'ALL' ? 'bg-brand text-white' : 'text-muted'}`}
              >
                All ({lecturesList.length})
              </button>
              <button
                onClick={() => setStatusFilter('READY')}
                className={`px-3 py-1.5 rounded-lg transition ${statusFilter === 'READY' ? 'bg-emerald-500 text-white' : 'text-muted'}`}
              >
                Analyzed
              </button>
              <button
                onClick={() => setStatusFilter('PROCESSING')}
                className={`px-3 py-1.5 rounded-lg transition ${statusFilter === 'PROCESSING' ? 'bg-brand text-white' : 'text-muted'}`}
              >
                Processing
              </button>
            </div>

          </div>

          <button
            onClick={() => navigate('/lectures')}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-brand px-4 text-xs font-bold text-white shadow-soft shrink-0"
          >
            <span>+ Upload Lecture</span>
          </button>
        </Card>


        {/* Lecture Timeline History List */}
        <div className="space-y-4">
          {filteredLectures.length === 0 ? (
            <Card className="p-8 text-center space-y-3">
              <Presentation className="h-10 w-10 text-muted mx-auto" />
              <h3 className="text-base font-extrabold text-ink dark:text-white">No lecture history found</h3>
              <p className="text-xs text-muted max-w-sm mx-auto">
                No recorded lecture sessions matched your current filter criteria.
              </p>
            </Card>
          ) : (
            filteredLectures.map((lec, index) => {
              const lecId = String(lec.id)
              const status = String(lec.status || 'COMPLETED').toUpperCase()
              const isReady = status === 'READY' || status === 'COMPLETED'

              return (
                <Card
                  key={lecId || index}
                  className="p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border border-line hover:border-brand/50 transition"
                >
                  <div className="flex items-start gap-4">
                    <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-brand/10 text-brand font-bold">
                      <Presentation className="h-5 w-5" />
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-extrabold text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="h-3 w-3" />
                          AI Analysis Complete
                        </span>

                        <span className="text-[10px] font-mono text-muted">
                          ID: {lecId.slice(0, 8)}
                        </span>
                      </div>

                      <h3 className="text-base font-extrabold text-ink dark:text-white">
                        {lec.title || `Lecture Session ${lecId.slice(0, 8)}`}
                      </h3>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {lec.lecture_date || 'Today'}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {lec.duration_minutes || 45} min
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <FileText className="h-3.5 w-3.5" />
                          {lec.total_words || 2400} words
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-line">
                    <button
                      onClick={() => setDeletingId(lecId)}
                      className="p-2 text-muted hover:text-danger transition rounded-lg border border-line"
                      title="Delete Lecture"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>

                    <button
                      onClick={() => {
                        setLectureId(lecId)
                        navigate('/results')
                      }}
                      className="inline-flex h-10 items-center gap-2 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-soft hover:bg-brand/90 transition"
                    >
                      <Sparkles className="h-4 w-4" />
                      <span>Open AI Results →</span>
                    </button>
                  </div>
                </Card>
              )
            })
          )}
        </div>

      </div>


      {/* DELETE CONFIRMATION MODAL */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-sm rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 text-center space-y-4">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-danger/10 text-danger mx-auto">
              <Trash2 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-extrabold text-ink dark:text-white">Delete this lecture?</h3>
            <p className="text-xs text-muted font-medium">This lecture and its transcript chunks will be permanently removed.</p>
            <div className="flex items-center justify-center gap-3 pt-2">
              <button onClick={() => setDeletingId(null)} className="h-10 rounded-xl border border-line px-5 text-xs font-bold text-muted">
                Cancel
              </button>
              <button
                onClick={() => deleteMutation.mutate(deletingId)}
                disabled={deleteMutation.isPending}
                className="h-10 rounded-xl bg-danger px-6 text-xs font-bold text-white shadow-soft disabled:opacity-60"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  )
}
