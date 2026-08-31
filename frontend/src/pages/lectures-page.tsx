import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Presentation, 
  Upload, 
  CheckCircle2, 
  Loader2, 
  AlertTriangle, 
  Plus, 
  BookOpen, 
  ArrowLeft,
  X,
  Eye,
  Trash2,
  Search,
  FileText,
  Clock,
  User,
  Sparkles,
  ArrowRight,
  Filter,
  Check,
  Radio,
<<<<<<< HEAD
  Share2,
  Video,
  Layers
=======
  Video
>>>>>>> 8e2376a (feat: Integrate Live Studio Capture, robust multi-format lecture uploads, and dynamic AI results)
} from 'lucide-react'
import { PageLayout } from '@/components/page-layout'
import { Card, EmptyState } from '@/components/ui'
import { lectureService } from '@/services/lecture-service'
import { useContextStore } from '@/store/context-store'
import { useAuthStore } from '@/store/auth-store'
import { friendlyError } from '@/hooks/use-api-query'
import LiveRecorder from '@/components/LiveRecorder'

import LiveRecorder from '@/components/LiveRecorder'
import HandoverContractModal from '@/components/HandoverContractModal'

export function LecturesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const { selectedCourseId, selectedCourseName, semester, setLectureId, selectedLectureId } = useContextStore()

  const [activeTabMode, setActiveTabMode] = useState<'LIST' | 'LIVE'>('LIST')
  const [handoverSessionId, setHandoverSessionId] = useState<string | null>(null)

  const [activeTabMode, setActiveTabMode] = useState<'LIST' | 'LIVE'>('LIST')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'READY' | 'PROCESSING' | 'FAILED'>('ALL')
  
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [uploadMode, setUploadMode] = useState<'FILE' | 'TEXT'>('FILE')
  const [title, setTitle] = useState('')
  const [lectureDate, setLectureDate] = useState(new Date().toISOString().split('T')[0])
  const [file, setFile] = useState<File | null>(null)
  const [rawText, setRawText] = useState('')
  const [clientError, setClientError] = useState<string | null>(null)

  const [viewingLectureId, setViewingLectureId] = useState<string | null>(null)
  const [deletingLectureId, setDeletingLectureId] = useState<string | null>(null)
  const [transcriptSearch, setTranscriptSearch] = useState('')

  // Fetch lectures for selected course with smart polling
  const { data: rawLectures, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['lectures', selectedCourseId],
    queryFn: () => lectureService.list(selectedCourseId || undefined),
    refetchInterval: (query) => {
      const items = (query.state.data as Array<Record<string, unknown>>) || []
      const isProcessing = items.some(item => {
        const s = String(item.status || '').toUpperCase()
        return s === 'PROCESSING' || s === 'PENDING' || s === 'UPLOADING'
      })
      return isProcessing ? 3000 : false
    }
  })

  // Fetch viewing lecture detail & chunks
  const { data: viewingLecture } = useQuery({
    queryKey: ['lecture-detail', viewingLectureId],
    queryFn: () => lectureService.get(viewingLectureId!),
    enabled: Boolean(viewingLectureId)
  })

  const { data: viewingChunks } = useQuery({
    queryKey: ['lecture-chunks', viewingLectureId],
    queryFn: () => lectureService.chunks(viewingLectureId!),
    enabled: Boolean(viewingLectureId)
  })

  // Upload lecture mutation
  const uploadMutation = useMutation({
    mutationFn: lectureService.upload,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['lectures'] })
      const newId = String(data.id || data.lecture_id || '')
      if (newId) {
        setLectureId(newId)
        setViewingLectureId(newId)
      }
      setIsUploadOpen(false)
      setTitle('')
      setFile(null)
      setRawText('')
      setClientError(null)
    }
  })

  // Delete lecture mutation
  const deleteMutation = useMutation({
    mutationFn: lectureService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lectures'] })
      setDeletingLectureId(null)
      if (viewingLectureId === deletingLectureId) {
        setViewingLectureId(null)
      }
    }
  })

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      setClientError('Lecture Title is required.')
      return
    }

    if (uploadMode === 'FILE' && !file) {
      setClientError('Please select an audio/video recording or transcript file.')
      return
    }

    if (uploadMode === 'TEXT' && !rawText.trim()) {
      setClientError('Please paste your transcript text.')
      return
    }

    setClientError(null)

    const formData = new FormData()
    formData.append('title', title.trim())
    formData.append('course_id', selectedCourseId || 'Course')
    formData.append('faculty_name', user?.full_name || 'Faculty Member')
    formData.append('lecture_date', lectureDate)

    if (uploadMode === 'FILE' && file) {
      formData.append('file', file)
    } else {
      formData.append('raw_text', rawText.trim())
    }

    uploadMutation.mutate(formData)
  }

  const lecturesList = (rawLectures as Array<Record<string, unknown>>) || []

  // Filter lectures
  const filteredLectures = lecturesList.filter(l => {
    const titleMatch = String(l.title || '').toLowerCase().includes(searchQuery.toLowerCase())
    const statusVal = String(l.status || 'READY').toUpperCase()
    if (statusFilter === 'READY') return titleMatch && ['READY', 'COMPLETED', 'TRANSCRIPT_READY'].includes(statusVal)
    if (statusFilter === 'PROCESSING') return titleMatch && ['PROCESSING', 'PENDING', 'UPLOADING'].includes(statusVal)
    if (statusFilter === 'FAILED') return titleMatch && statusVal === 'FAILED'
    return titleMatch
  })

  const chunksList = (viewingChunks as Array<Record<string, unknown>>) || []
  const filteredChunks = chunksList.filter(c => 
    String(c.text || '').toLowerCase().includes(transcriptSearch.toLowerCase()) ||
    String(c.speaker || '').toLowerCase().includes(transcriptSearch.toLowerCase())
  )

  return (
    <PageLayout
      title="Lecture Workflow & Capture Studio"
      description="Record live lectures with webcam/microphone or upload lecture files. Converts audio/video streams into structured transcripts ready for AI analysis."
      hideContextBadges={true}
      actions={
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTabMode(activeTabMode === 'LIVE' ? 'LIST' : 'LIVE')}
            className={`inline-flex h-11 items-center gap-2 rounded-xl px-4 text-xs font-bold transition shadow-soft ${activeTabMode === 'LIVE' ? 'bg-rose-500 text-white' : 'border border-line bg-canvas text-ink dark:text-white hover:bg-surface'}`}
          >
            <Radio className="h-4 w-4 animate-pulse text-rose-400" />
            <span>{activeTabMode === 'LIVE' ? '← Back to Lectures Workspace' : '🔴 Live Studio Capture'}</span>
          </button>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-5 text-sm font-bold text-white shadow-soft transition hover:bg-brand/90 hover:scale-105 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            <span>+ Upload Lecture File</span>
          </button>
        </div>
      }
    >
      <div className="space-y-6">

        {/* Tab Switcher Banner */}
        <div className="flex items-center gap-2 bg-canvas border border-line p-1.5 rounded-2xl">
          <button
            onClick={() => setActiveTabMode('LIST')}
            className={`flex-1 py-2.5 px-4 text-xs font-extrabold rounded-xl transition flex items-center justify-center gap-2 ${activeTabMode === 'LIST' ? 'bg-brand text-white shadow-soft' : 'text-muted dark:text-slate-300 hover:text-ink'}`}
          >
            <FileText className="h-4 w-4" />
            <span>Uploaded Lectures Workspace & Ingestion</span>
          </button>

          <button
            onClick={() => setActiveTabMode('LIVE')}
            className={`flex-1 py-2.5 px-4 text-xs font-extrabold rounded-xl transition flex items-center justify-center gap-2 ${activeTabMode === 'LIVE' ? 'bg-rose-600 text-white shadow-soft' : 'text-muted dark:text-slate-300 hover:text-ink'}`}
          >
            <Video className="h-4 w-4" />
            <span>Member 1 Live Studio Capture (Webcam, Mic, Smart Board)</span>
          </button>
        </div>

        {activeTabMode === 'LIVE' ? (
          <div className="rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 shadow-soft space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div>
                <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider block">MEMBER 1 LIVE CAPTURE STUDIO</span>
                <h2 className="text-lg font-extrabold text-ink dark:text-white">Real-Time Classroom Recorder</h2>
              </div>
              <span className="text-xs font-semibold text-muted bg-canvas border border-line px-3 py-1 rounded-full">
                Auto-streams 5s slices to FastAPI Backend
              </span>
            </div>

            <LiveRecorder
              onSessionCreated={(sessionData: any) => {
                queryClient.invalidateQueries({ queryKey: ['lectures'] })
                const newId = String(sessionData?.session_id || sessionData?.id || '')
                if (newId) {
                  setLectureId(newId)
                  setHandoverSessionId(newId)
                }
                setActiveTabMode('LIST')
              }}
            />
          </div>
        ) : (
          <>
            {/* PROMINENT SELECTED COURSE BAR */}
            <div className="rounded-2xl border border-line bg-surface dark:bg-slate-900 p-5 shadow-soft flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-soft text-brand shrink-0">
                  <BookOpen className="h-6 w-6" />
                </div>
                <div>
                  <span className="text-[10px] font-mono font-bold text-brand uppercase tracking-wider block">ACTIVE COURSE CONTEXT</span>
                  <h3 className="text-lg font-extrabold text-ink dark:text-white leading-snug">
                    {selectedCourseName || (selectedCourseId ? 'Active Course' : 'No course selected')}
                  </h3>
                  <p className="text-xs text-muted dark:text-slate-300 font-medium">
                    {selectedCourseId ? (semester || 'Semester 6 · Academic Year 2026-2027') : 'Create or select a course from the Courses page to manage lectures'}
                  </p>
                </div>
              </div>

              <Link
                to="/courses"
                className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-canvas px-4 text-xs font-bold text-ink dark:text-white hover:bg-surface transition shrink-0"
              >
                <span>Change Course</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

        {/* SEARCH & FILTER BAR */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-muted" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search lectures by title..."
              className="h-10 w-full rounded-xl border border-line bg-canvas pl-10 pr-4 text-xs font-semibold text-ink dark:text-white outline-none focus:border-brand"
            />
          </div>

          <div className="flex items-center gap-1 bg-canvas border border-line p-1 rounded-xl w-full sm:w-auto">
            <button
              onClick={() => setStatusFilter('ALL')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${statusFilter === 'ALL' ? 'bg-brand text-white' : 'text-muted dark:text-slate-300'}`}
            >
              All ({lecturesList.length})
            </button>
            <button
              onClick={() => setStatusFilter('READY')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${statusFilter === 'READY' ? 'bg-teal-500 text-white' : 'text-muted dark:text-slate-300'}`}
            >
              Ready
            </button>
            <button
              onClick={() => setStatusFilter('PROCESSING')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${statusFilter === 'PROCESSING' ? 'bg-amber-500 text-white' : 'text-muted dark:text-slate-300'}`}
            >
              Processing
            </button>
          </div>
        </div>

        {/* LECTURE CARDS GRID */}
        {isLoading ? (
          <div className="grid min-h-[300px] place-items-center rounded-3xl border border-line bg-surface p-8 text-center text-sm font-semibold text-muted">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-7 w-7 animate-spin text-brand" />
              <span>Loading lectures workspace…</span>
            </div>
          </div>
        ) : isError ? (
          <div className="rounded-3xl border border-danger/20 bg-danger/10 p-6 text-center text-xs font-semibold text-danger">
            Failed to load lectures. <button onClick={() => refetch()} className="underline font-bold">Retry</button>
          </div>
        ) : filteredLectures.length === 0 ? (
          <EmptyState
            title="No lectures found"
            description="Upload your delivered lecture recording or transcript to begin transcript segmentation, curriculum mapping, and teaching analysis."
            action={
              <button
                onClick={() => setIsUploadOpen(true)}
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-6 text-sm font-bold text-white shadow-soft hover:bg-brand/90"
              >
                <Plus className="h-4 w-4" />
                <span>Upload First Lecture</span>
              </button>
            }
          />
        ) : (
          <div className="space-y-4">
            <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase tracking-wider block">
              LECTURES ({filteredLectures.length})
            </span>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredLectures.map((l) => {
                const lecId = String(l.id || l.lecture_id)
                const lecTitle = String(l.title || 'Delivered Lecture Session')
                const lecDate = String(l.lecture_date || 'Today')
                const lecDuration = Number(l.duration_minutes || 45)
                const statusStr = String(l.status || 'READY').toUpperCase()

                const isReady = ['READY', 'COMPLETED', 'TRANSCRIPT_READY'].includes(statusStr)
                const isProcessing = ['PROCESSING', 'PENDING', 'UPLOADING'].includes(statusStr)
                const isFailed = statusStr === 'FAILED'

                return (
                  <Card
                    key={lecId}
                    className="group relative flex flex-col justify-between p-6 shadow-soft hover:border-brand/40 transition duration-200"
                  >
                    <div className="space-y-4">
                      {/* Top Bar */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-soft text-brand shrink-0">
                            <Presentation className="h-5 w-5" />
                          </div>
                          <div>
                            <h3 className="font-extrabold text-lg text-ink dark:text-white leading-snug group-hover:text-brand transition">
                              {lecTitle}
                            </h3>
                            <div className="flex items-center gap-3 text-xs font-medium text-muted dark:text-slate-300 mt-1">
                              <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> {lecDuration} min</span>
                              <span>·</span>
                              <span>{lecDate}</span>
                            </div>
                          </div>
                        </div>

                        <button
                          onClick={() => setDeletingLectureId(lecId)}
                          className="p-2 rounded-xl border border-line bg-canvas text-muted hover:text-danger hover:border-danger/30 transition shrink-0"
                          title="Delete lecture"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>

                      {/* Visual Processing Journey Pipeline */}
                      <div className="rounded-xl border border-line bg-canvas p-3.5 space-y-2">
                        <div className="flex items-center justify-between text-[11px] font-mono font-bold text-muted dark:text-slate-300">
                          <span>INTELLIGENCE PIPELINE</span>
                          <span className={isReady ? 'text-teal-400' : isProcessing ? 'text-amber-400' : 'text-danger'}>
                            {isReady ? '● Transcript Ready' : isProcessing ? '◌ Processing...' : '! Failed'}
                          </span>
                        </div>

                        <div className="grid grid-cols-4 gap-1 text-[10px] font-bold text-center">
                          <div className="rounded bg-teal-500/20 text-teal-300 py-1 flex items-center justify-center gap-1">
                            <Check className="h-3 w-3" /> Capture
                          </div>
                          <div className="rounded bg-teal-500/20 text-teal-300 py-1 flex items-center justify-center gap-1">
                            <Check className="h-3 w-3" /> Process
                          </div>
                          <div className={`rounded py-1 flex items-center justify-center gap-1 ${isReady ? 'bg-teal-500/20 text-teal-300' : 'bg-amber-500/20 text-amber-300'}`}>
                            {isReady ? <Check className="h-3 w-3" /> : <Loader2 className="h-3 w-3 animate-spin" />} Transcript
                          </div>
                          <div className={`rounded py-1 ${isReady ? 'bg-teal-500/20 text-teal-300 font-extrabold' : 'bg-line/40 text-muted'}`}>
                            {isReady ? '✓ Ready' : '○ Pending'}
                          </div>
                        </div>
                      </div>

                    </div>

                    {/* Footer Actions */}
                    <div className="mt-5 pt-4 border-t border-line flex items-center justify-between">
                      <button
                        onClick={() => {
                          setLectureId(lecId)
                          setViewingLectureId(lecId)
                        }}
                        className="inline-flex items-center gap-2 text-xs font-extrabold text-brand hover:underline"
                      >
                        <Eye className="h-4 w-4" />
                        <span>View Lecture & Transcript</span>
                      </button>

                      {isReady && (
                        <button
                          onClick={() => {
                            setLectureId(lecId)
                            navigate('/coverage')
                          }}
                          className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-400 hover:underline"
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          <span>AI Analysis →</span>
                        </button>
                      )}
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>
        )}
      </>
    )}

        {/* LECTURE UPLOAD MODAL */}
        {isUploadOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <div className="relative w-full max-w-lg rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-8 shadow-2xl text-ink dark:text-white space-y-6">
              
              <div className="flex items-center justify-between border-b border-line pb-4">
                <div>
                  <span className="text-xs font-mono font-bold text-brand uppercase">LECTURE INGESTION</span>
                  <h2 className="text-xl font-extrabold text-ink dark:text-white">+ Upload Lecture</h2>
                </div>
                <button
                  onClick={() => setIsUploadOpen(false)}
                  className="rounded-xl border border-line p-2 text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Mode Toggle (File Recording vs Text Transcript) */}
              <div className="flex items-center gap-2 bg-canvas border border-line p-1 rounded-xl">
                <button
                  type="button"
                  onClick={() => setUploadMode('FILE')}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg transition ${uploadMode === 'FILE' ? 'bg-brand text-white shadow-soft' : 'text-muted dark:text-slate-300'}`}
                >
                  Audio / Video / Document File
                </button>
                <button
                  type="button"
                  onClick={() => setUploadMode('TEXT')}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg transition ${uploadMode === 'TEXT' ? 'bg-brand text-white shadow-soft' : 'text-muted dark:text-slate-300'}`}
                >
                  Paste Transcript Text
                </button>
              </div>

              <form onSubmit={handleUploadSubmit} className="space-y-4">
                {/* Title */}
                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    Lecture Title <span className="text-danger">*</span>
                  </label>
                  <input
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Introduction to TCP Protocol / Agentic AI Systems"
                    className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                  />
                </div>

                {/* Course (Pre-filled read-only display) */}
                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    Course (Inherited)
                  </label>
                  <input
                    disabled
                    value={selectedCourseName || (selectedCourseId ? "Active Course" : "No Course Selected")}
                    className="h-11 w-full rounded-xl border border-line bg-canvas/50 px-3.5 text-sm font-bold text-muted cursor-not-allowed"
                  />
                </div>

                {/* Lecture Date */}
                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    Lecture Date
                  </label>
                  <input
                    type="date"
                    value={lectureDate}
                    onChange={(e) => setLectureDate(e.target.value)}
                    className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                  />
                </div>

                {/* File Dropzone */}
                {uploadMode === 'FILE' ? (
                  <div>
                    <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                      Lecture Recording / File <span className="text-danger">*</span>
                    </label>
                    <div className="rounded-2xl border border-dashed border-line bg-canvas p-6 text-center">
                      <input
                        type="file"
                        accept=".mp3,.wav,.m4a,.mp4,.pdf,.docx,.txt,.json"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        className="hidden"
                        id="lecture-file-input"
                      />
                      <label htmlFor="lecture-file-input" className="cursor-pointer space-y-2 block">
                        <Upload className="h-8 w-8 text-brand mx-auto" />
                        {file ? (
                          <span className="text-xs font-bold text-teal-400 block truncate">
                            ✓ {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                          </span>
                        ) : (
                          <span className="text-xs font-bold text-muted dark:text-slate-300 block">
                            Drop recording file here or browse (MP3, WAV, MP4, PDF, TXT, JSON)
                          </span>
                        )}
                      </label>
                    </div>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                      Raw Lecture Transcript <span className="text-danger">*</span>
                    </label>
                    <textarea
                      rows={6}
                      value={rawText}
                      onChange={(e) => setRawText(e.target.value)}
                      placeholder="Paste the spoken transcript here (e.g., 'Faculty: Today we will explore TCP windowing and congestion control...')"
                      className="w-full rounded-2xl border border-line bg-canvas p-3.5 text-xs font-mono text-ink dark:text-white outline-none focus:border-brand leading-relaxed"
                    />
                  </div>
                )}

                {/* Error */}
                {(clientError || uploadMutation.error) && (
                  <div className="rounded-xl border border-danger/20 bg-danger/10 p-3 text-xs font-bold text-danger">
                    {clientError || friendlyError(uploadMutation.error)}
                  </div>
                )}

                {/* Submit buttons */}
                <div className="pt-2 flex items-center justify-end gap-3 border-t border-line">
                  <button
                    type="button"
                    onClick={() => setIsUploadOpen(false)}
                    className="h-11 rounded-xl border border-line bg-canvas px-5 text-xs font-bold text-muted dark:text-slate-300 hover:text-ink transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={uploadMutation.isPending}
                    className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-6 text-xs font-bold text-white shadow-soft hover:bg-brand/90 disabled:opacity-60 transition"
                  >
                    {uploadMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Processing Lecture…</span>
                      </>
                    ) : (
                      <span>Upload & Process Lecture</span>
                    )}
                  </button>
                </div>
              </form>

            </div>
          </div>
        )}

        {/* LECTURE DETAIL & TRANSCRIPT MODAL */}
        {viewingLectureId && viewingLecture && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <div className="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-8 shadow-2xl text-ink dark:text-white space-y-5 overflow-hidden">
              
              {/* Header */}
              <div className="flex items-center justify-between border-b border-line pb-4 shrink-0">
                <div className="flex items-center gap-3">
                  <div className="grid h-11 w-11 place-items-center rounded-2xl bg-brand text-white">
                    <Presentation className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-xs font-mono font-bold text-brand uppercase">LECTURE TRANSCRIPT & INTELLIGENCE</span>
                    <h2 className="text-xl font-extrabold text-ink dark:text-white">
                      {String(viewingLecture.title || 'Lecture Session')}
                    </h2>
                  </div>
                </div>

                <button
                  onClick={() => setViewingLectureId(null)}
                  className="rounded-xl border border-line p-2 text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Scrollable Container */}
              <div className="overflow-y-auto space-y-5 pr-1">
                {/* Processing Pipeline Journey */}
                <div className="rounded-2xl border border-teal-400/30 bg-teal-500/10 p-4">
                  <span className="text-xs font-mono font-bold text-teal-300 uppercase tracking-wider block mb-2">
                    ✓ PROCESSING JOURNEY COMPLETE
                  </span>
                  <div className="grid grid-cols-4 gap-2 text-xs font-bold text-center">
                    <div className="rounded-xl bg-teal-500/20 text-teal-200 p-2">✓ Uploaded</div>
                    <div className="rounded-xl bg-teal-500/20 text-teal-200 p-2">✓ Processed</div>
                    <div className="rounded-xl bg-teal-500/20 text-teal-200 p-2">✓ Transcript Ready</div>
                    <div className="rounded-xl bg-teal-500/20 text-teal-200 p-2 font-extrabold">✓ Ready for AI</div>
                  </div>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="rounded-xl border border-line bg-canvas p-3">
                    <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">DURATION</span>
                    <span className="font-extrabold text-ink dark:text-white">{String(viewingLecture.duration_minutes || 45)} min</span>
                  </div>
                  <div className="rounded-xl border border-line bg-canvas p-3">
                    <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">WORDS</span>
                    <span className="font-extrabold text-brand">{String(viewingLecture.total_words || chunksList.reduce((acc, c) => acc + Number(c.word_count || 0), 0))} words</span>
                  </div>
                  <div className="rounded-xl border border-line bg-canvas p-3">
                    <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">CHUNKS</span>
                    <span className="font-extrabold text-teal-400">{chunksList.length} chunks</span>
                  </div>
                  <div className="rounded-xl border border-line bg-canvas p-3">
                    <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">DATE</span>
                    <span className="font-extrabold text-ink dark:text-white">{String(viewingLecture.lecture_date || 'Today')}</span>
                  </div>
                </div>

                {/* Transcript Chunks Display */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider">
                      STRUCTURED TRANSCRIPT & CURRICULUM TOPIC MAPPINGS ({filteredChunks.length})
                    </span>

                    <div className="relative w-48">
                      <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-muted" />
                      <input
                        value={transcriptSearch}
                        onChange={(e) => setTranscriptSearch(e.target.value)}
                        placeholder="Search transcript..."
                        className="h-8 w-full rounded-lg border border-line bg-canvas pl-8 pr-2 text-[11px] font-medium text-ink dark:text-white outline-none focus:border-brand"
                      />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-line bg-canvas p-4 space-y-3 max-h-72 overflow-y-auto">
                    {filteredChunks.length === 0 ? (
                      <p className="text-xs text-muted italic text-center py-4">No matching transcript segments found.</p>
                    ) : (
                      filteredChunks.map((chunk, idx) => {
                        const speaker = String(chunk.speaker || 'Faculty')
                        const startTime = Number(chunk.start_time || 0)
                        const endTime = Number(chunk.end_time || 0)
                        const textVal = String(chunk.text || '')
                        const formatTime = (sec: number) => {
                          const m = Math.floor(sec / 60)
                          const s = Math.floor(sec % 60)
                          return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
                        }

                        return (
                          <div key={idx} className="rounded-xl border border-line/60 bg-surface dark:bg-slate-900/80 p-3.5 space-y-2">
                            <div className="flex items-center justify-between text-[11px]">
                              <div className="flex items-center gap-2">
                                <span className="rounded bg-brand-soft font-mono font-extrabold text-brand px-2 py-0.5">
                                  {formatTime(startTime)} - {formatTime(endTime)}
                                </span>
                                <span className="font-bold text-ink dark:text-white">{speaker}</span>
                              </div>
                              <span className="text-[10px] font-mono text-muted">Chunk #{String(chunk.chunk_index || idx + 1)}</span>
                            </div>

                            <p className="text-xs font-sans text-ink dark:text-slate-200 leading-relaxed">
                              "{textVal}"
                            </p>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between border-t border-line pt-4 shrink-0">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => {
                      setDeletingLectureId(viewingLectureId)
                    }}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-danger hover:underline"
                  >
                    <Trash2 className="h-4 w-4" />
                    <span>Delete Lecture</span>
                  </button>

                  <button
                    onClick={() => {
                      setHandoverSessionId(viewingLectureId)
                    }}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 rounded-lg hover:bg-indigo-500/20"
                  >
                    <Share2 className="h-4 w-4" />
                    <span>Inspect Member 1 Handover Payload</span>
                  </button>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setViewingLectureId(null)}
                    className="h-10 rounded-xl border border-line bg-canvas px-5 text-xs font-bold text-muted hover:text-ink"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      setViewingLectureId(null)
                      navigate('/results')
                    }}
                    className="inline-flex h-10 items-center gap-2 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-soft hover:bg-brand/90"
                  >
                    <Sparkles className="h-4 w-4" />
                    <span>Open AI Intelligence Analysis →</span>
                  </button>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* DELETE CONFIRMATION MODAL */}
        {deletingLectureId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <div className="relative w-full max-w-sm rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 shadow-2xl text-ink dark:text-white space-y-4 text-center">
              <div className="grid h-12 w-12 place-items-center rounded-2xl bg-danger/10 text-danger mx-auto">
                <Trash2 className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-extrabold text-ink dark:text-white">Delete this lecture?</h3>
              <p className="text-xs text-muted dark:text-slate-300 font-bold leading-relaxed">
                This lecture session and its transcript chunks will be deleted.
              </p>

              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setDeletingLectureId(null)}
                  className="h-10 rounded-xl border border-line bg-canvas px-5 text-xs font-bold text-muted hover:text-ink"
                >
                  Cancel
                </button>
                <button
                  onClick={() => deleteMutation.mutate(deletingLectureId)}
                  disabled={deleteMutation.isPending}
                  className="h-10 rounded-xl bg-danger px-6 text-xs font-bold text-white shadow-soft hover:bg-danger/90 disabled:opacity-60"
                >
                  {deleteMutation.isPending ? 'Deleting…' : 'Confirm Delete'}
                </button>
              </div>
            </div>
          </div>
        )}

        </>
        )}

        {/* MEMBER 1 HANDOVER CONTRACT INSPECTION MODAL */}
        {handoverSessionId && (
          <HandoverContractModal
            sessionId={handoverSessionId}
            onClose={() => setHandoverSessionId(null)}
          />
        )}

      </div>
    </PageLayout>
  )
}
