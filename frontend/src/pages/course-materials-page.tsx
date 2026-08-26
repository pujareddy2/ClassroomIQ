import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  FileText, 
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
  Presentation,
  BarChart3,
  HelpCircle
} from 'lucide-react'
import { PageLayout } from '@/components/page-layout'
import { Card, EmptyState } from '@/components/ui'
import { referenceService } from '@/services/reference-service'
import { useContextStore } from '@/store/context-store'
import { useAuthStore } from '@/store/auth-store'
import { friendlyError } from '@/hooks/use-api-query'

export function CourseMaterialsPage() {
  const { courseId: paramCourseId } = useParams<{ courseId?: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const { selectedCourseId, semester } = useContextStore()

  const courseId = paramCourseId || selectedCourseId || undefined

  const [activeTab, setActiveTab] = useState<'overview' | 'materials'>('materials')
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [viewingMaterial, setViewingMaterial] = useState<Record<string, unknown> | null>(null)
  const [deletingMaterialId, setDeletingMaterialId] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [docType, setDocType] = useState<'FACULTY_NOTES' | 'REFERENCE_BOOK' | 'PPT' | 'LAB_MANUAL' | 'ASSIGNMENT' | 'QUESTION_BANK'>('FACULTY_NOTES')
  const [file, setFile] = useState<File | null>(null)
  const [clientError, setClientError] = useState<string | null>(null)

  // Fetch reference materials for this course with smart polling
  const { data: materials, isLoading, isError, refetch } = useQuery({
    queryKey: ['reference-materials', courseId],
    queryFn: () => referenceService.list(courseId),
    enabled: Boolean(courseId),
    refetchInterval: (query) => {
      const items = (query.state.data as Array<Record<string, unknown>>) || []
      const isProcessing = items.some(item => {
        const status = String(item.processing_status || '').toUpperCase()
        return status === 'PROCESSING' || status === 'PENDING'
      })
      return isProcessing ? 3000 : false
    }
  })

  // Upload material mutation
  const uploadMutation = useMutation({
    mutationFn: referenceService.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference-materials', courseId] })
      setIsUploadOpen(false)
      setTitle('')
      setFile(null)
      setClientError(null)
    }
  })

  // Delete material mutation
  const deleteMutation = useMutation({
    mutationFn: referenceService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reference-materials', courseId] })
      setDeletingMaterialId(null)
      if (viewingMaterial && String(viewingMaterial.id) === deletingMaterialId) {
        setViewingMaterial(null)
      }
    }
  })

  const handleUpload = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      setClientError('Material Title is required.')
      return
    }
    if (!file) {
      setClientError('Please select a file to upload.')
      return
    }

    if (file.size > 50 * 1024 * 1024) {
      setClientError('File size must be less than 50MB.')
      return
    }

    const validExtensions = ['.pdf', '.docx', '.txt', '.ppt', '.pptx']
    const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!validExtensions.includes(fileExt)) {
      setClientError('This file type isn\'t supported. Please upload a PDF, DOCX, TXT, or PPT file.')
      return
    }

    setClientError(null)

    const formData = new FormData()
    formData.append('course_name', courseId || 'Course')
    formData.append('academic_year', '2026-2027')
    formData.append('semester', '6')
    formData.append('faculty_name', user?.full_name || 'Faculty Member')
    formData.append('title', title.trim())
    formData.append('document_type', docType)
    formData.append('file', file)

    uploadMutation.mutate(formData)
  }

  const materialsList = (materials as Array<Record<string, unknown>>) || []
  const readyCount = materialsList.filter(m => {
    const s = String(m.processing_status || '').toUpperCase()
    return ['COMPLETED', 'READY', 'EMBEDDED', 'TEXT_EXTRACTED'].includes(s)
  }).length
  const processingCount = materialsList.filter(m => ['PROCESSING', 'PENDING', 'UPLOADED'].includes(String(m.processing_status || '').toUpperCase())).length

  return (
    <PageLayout
      title="Course Materials Workspace"
      description="Add the notes and reference materials ClassroomIQ should use when analyzing your lectures."
      hideContextBadges={true}
      actions={
        <div className="flex items-center gap-3">
          <Link
            to="/courses"
            className="inline-flex h-11 items-center gap-2 rounded-xl border border-line bg-surface px-4 text-xs font-bold text-ink dark:text-white hover:bg-canvas transition"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>All Courses</span>
          </Link>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-5 text-sm font-bold text-white shadow-soft transition hover:bg-brand/90 hover:scale-105 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            <span>Upload Material</span>
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        
        {/* Navigation Tabs (Overview, Materials, Lectures, Insights) */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                activeTab === 'overview'
                  ? 'bg-brand text-white shadow-soft'
                  : 'text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('materials')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                activeTab === 'materials'
                  ? 'bg-brand text-white shadow-soft'
                  : 'text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white'
              }`}
            >
              Materials ({materialsList.length})
            </button>
            <button
              onClick={() => navigate('/lectures')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-muted dark:text-slate-300 hover:text-brand hover:bg-brand-soft/50 transition"
              title="Upload and manage lecture transcripts"
            >
              <Presentation className="h-3.5 w-3.5" />
              <span>Lectures</span>
            </button>
            <button
              onClick={() => navigate('/analytics')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-muted dark:text-slate-300 hover:text-brand hover:bg-brand-soft/50 transition"
              title="View lecture analysis & AI insights"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span>Insights</span>
            </button>
          </div>

          <div className="flex items-center gap-1 text-[11px] font-mono text-muted dark:text-slate-400">
            <HelpCircle className="h-3.5 w-3.5 text-brand" />
            <span>Lectures = Upload speech audio/transcript · Insights = View AI analysis</span>
          </div>
        </div>

        {/* Readiness Banner */}
        {materialsList.length > 0 && (
          <div className={`rounded-2xl border p-5 transition flex flex-col sm:flex-row items-center justify-between gap-4 ${
            processingCount > 0
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-200'
              : 'border-teal-400/30 bg-teal-500/10 text-teal-300'
          }`}>
            <div className="flex items-center gap-3">
              {processingCount > 0 ? (
                <Loader2 className="h-6 w-6 text-amber-400 animate-spin shrink-0" />
              ) : (
                <CheckCircle2 className="h-6 w-6 text-teal-400 shrink-0" />
              )}
              <div>
                <h4 className="font-extrabold text-sm sm:text-base text-ink dark:text-white">
                  {processingCount > 0
                    ? '⟳ Preparing course materials...'
                    : '✓ Course knowledge base ready'}
                </h4>
                <p className="text-xs text-muted dark:text-slate-200 font-semibold mt-0.5">
                  {processingCount > 0
                    ? `${processingCount} material(s) being prepared by ClassroomIQ backend.`
                    : 'ClassroomIQ can now use these materials as reference when analyzing your lectures.'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono font-bold shrink-0">
              <span className="bg-canvas border border-line px-3 py-1 rounded-full text-ink dark:text-white">
                {readyCount} / {materialsList.length} Ready
              </span>
            </div>
          </div>
        )}

        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <Card className="p-6 space-y-4">
            <h3 className="text-lg font-bold text-ink dark:text-white">Course Knowledge Overview</h3>
            <p className="text-xs text-muted dark:text-slate-300 font-semibold leading-relaxed">
              Upload your syllabus, lecture notes, textbooks, or reference PDFs. ClassroomIQ preprocesses and indexes your course materials so it can cross-reference spoken lecture content against your authoritative references during analysis.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="rounded-xl border border-line bg-canvas p-4 text-center">
                <span className="text-2xl font-extrabold text-brand block">{materialsList.length}</span>
                <span className="text-xs font-semibold text-muted dark:text-slate-300">Total Materials</span>
              </div>
              <div className="rounded-xl border border-line bg-canvas p-4 text-center">
                <span className="text-2xl font-extrabold text-teal-400 block">{readyCount}</span>
                <span className="text-xs font-semibold text-muted dark:text-slate-300">Ready for Analysis</span>
              </div>
              <div className="rounded-xl border border-line bg-canvas p-4 text-center">
                <span className="text-2xl font-extrabold text-amber-400 block">{processingCount}</span>
                <span className="text-xs font-semibold text-muted dark:text-slate-300">In Preparation</span>
              </div>
            </div>
          </Card>
        )}

        {/* MATERIALS TAB */}
        {activeTab === 'materials' && (
          <div>
            {isLoading ? (
              <div className="grid min-h-[300px] place-items-center rounded-3xl border border-line bg-surface p-8 text-center text-sm font-semibold text-muted">
                Loading course materials…
              </div>
            ) : isError ? (
              <div className="rounded-3xl border border-danger/20 bg-danger/10 p-6 text-center text-xs font-semibold text-danger">
                Failed to load materials. <button onClick={() => refetch()} className="underline font-bold">Retry</button>
              </div>
            ) : materialsList.length === 0 ? (
              <EmptyState
                title="Your course materials are empty"
                description="Upload your notes, syllabus, or reference PDFs so ClassroomIQ can understand your course before analyzing your lectures."
                action={
                  <button
                    onClick={() => setIsUploadOpen(true)}
                    className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-6 text-sm font-bold text-white shadow-soft hover:bg-brand/90"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Upload Material</span>
                  </button>
                }
              />
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-muted dark:text-slate-300 uppercase tracking-wider">
                    COURSE REFERENCE MATERIALS ({materialsList.length})
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {materialsList.map((item, idx) => {
                    const mat = item as Record<string, unknown>
                    const matId = String(mat.id || idx)
                    const matTitle = String(mat.title || mat.file_name || `Material #${idx + 1}`)
                    const matType = String(mat.document_type || 'FACULTY_NOTES')
                    const matFileName = String(mat.file_name || matTitle)
                    const matStatus = String(mat.processing_status || 'READY').toUpperCase()
                    const createdAt = mat.created_at ? new Date(String(mat.created_at)).toLocaleDateString() : 'Today'
                    const bytes = Number(mat.file_size || 0)
                    const sizeMb = bytes > 0 ? (bytes / (1024 * 1024)).toFixed(2) + ' MB' : 'Uploaded PDF'

                    const isReady = ['COMPLETED', 'READY', 'EMBEDDED', 'TEXT_EXTRACTED'].includes(matStatus)
                    const isProcessing = ['PROCESSING', 'PENDING', 'UPLOADED'].includes(matStatus)
                    const isFailed = matStatus === 'FAILED'

                    return (
                      <Card
                        key={matId}
                        className="group flex flex-col justify-between p-5 shadow-soft hover:border-brand/40 transition"
                      >
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex items-center gap-3">
                              <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-soft text-brand shrink-0">
                                <FileText className="h-5 w-5" />
                              </div>
                              <div>
                                <h4 className="font-extrabold text-base text-ink dark:text-white leading-snug group-hover:text-brand transition">
                                  {matTitle}
                                </h4>
                                <span className="text-[11px] font-mono text-muted dark:text-slate-300 font-semibold block truncate max-w-xs">
                                  {matFileName}
                                </span>
                              </div>
                            </div>

                            {/* View Content & Delete Buttons */}
                            <div className="flex items-center gap-1 shrink-0">
                              <button
                                onClick={() => setViewingMaterial(mat)}
                                className="p-2 rounded-lg border border-line bg-canvas text-muted hover:text-brand transition"
                                title="View details and content"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => setDeletingMaterialId(matId)}
                                className="p-2 rounded-lg border border-line bg-canvas text-muted hover:text-danger hover:border-danger/30 transition"
                                title="Remove material"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-2 text-xs">
                            <span className="rounded-md border border-line bg-canvas px-2.5 py-0.5 font-mono font-bold text-muted dark:text-slate-300 uppercase">
                              {matType.replace('_', ' ')}
                            </span>
                            <span className="text-xs text-muted dark:text-slate-300 font-semibold">
                              {sizeMb} · Uploaded {createdAt}
                            </span>
                          </div>
                        </div>

                        {/* Status Footer */}
                        <div className="mt-4 pt-3 border-t border-line flex items-center justify-between text-xs font-bold">
                          {isReady ? (
                            <span className="inline-flex items-center gap-1.5 text-teal-400">
                              <CheckCircle2 className="h-4 w-4" />
                              <span>Ready for lecture analysis</span>
                            </span>
                          ) : isProcessing ? (
                            <span className="inline-flex items-center gap-1.5 text-amber-400">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              <span>Preparing your material...</span>
                            </span>
                          ) : isFailed ? (
                            <span className="inline-flex items-center gap-1.5 text-danger">
                              <AlertTriangle className="h-4 w-4" />
                              <span>Processing failed</span>
                            </span>
                          ) : (
                            <span className="text-teal-400 font-bold">✓ Ready ({matStatus})</span>
                          )}

                          <button
                            onClick={() => setViewingMaterial(mat)}
                            className="text-xs font-bold text-brand hover:underline"
                          >
                            View Content →
                          </button>
                        </div>
                      </Card>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* VIEW MATERIAL CONTENT MODAL */}
        {viewingMaterial && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <div className="relative w-full max-w-xl rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-8 shadow-2xl text-ink dark:text-white space-y-5">
              <div className="flex items-center justify-between border-b border-line pb-4">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand text-white">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <span className="text-xs font-mono font-bold text-brand uppercase">MATERIAL INSPECTION</span>
                    <h3 className="text-xl font-extrabold text-ink dark:text-white">
                      {String(viewingMaterial.title || viewingMaterial.file_name)}
                    </h3>
                  </div>
                </div>

                <button
                  onClick={() => setViewingMaterial(null)}
                  className="rounded-xl border border-line p-2 text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Material Details Table */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-xl border border-line bg-canvas p-3">
                  <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">FILE NAME</span>
                  <span className="font-bold text-ink dark:text-white truncate block">{String(viewingMaterial.file_name || '—')}</span>
                </div>
                <div className="rounded-xl border border-line bg-canvas p-3">
                  <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">DOCUMENT TYPE</span>
                  <span className="font-bold text-brand uppercase">{String(viewingMaterial.document_type || 'FACULTY_NOTES')}</span>
                </div>
                <div className="rounded-xl border border-line bg-canvas p-3">
                  <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">STATUS</span>
                  <span className="font-bold text-teal-400">{String(viewingMaterial.processing_status || 'READY')}</span>
                </div>
                <div className="rounded-xl border border-line bg-canvas p-3">
                  <span className="text-muted dark:text-slate-400 font-bold block mb-0.5">UPLOADED DATE</span>
                  <span className="font-bold text-ink dark:text-white">{viewingMaterial.created_at ? new Date(String(viewingMaterial.created_at)).toLocaleString() : 'Recent'}</span>
                </div>
              </div>

              {/* Extracted Text Preview Container */}
              <div className="space-y-2">
                <span className="text-xs font-mono font-bold text-brand uppercase tracking-wider block">
                  INDEXED REFERENCE EXTRACT PREVIEW
                </span>
                <div className="rounded-2xl border border-line bg-canvas p-4 text-xs font-mono text-slate-300 max-h-48 overflow-y-auto leading-relaxed border-inner">
                  {viewingMaterial.extracted_text ? (
                    <p className="whitespace-pre-wrap">{String(viewingMaterial.extracted_text)}</p>
                  ) : (
                    <p className="text-muted italic">
                      ✓ Material text has been parsed and indexed by ClassroomIQ RAG retrieval engine for lecture cross-referencing.
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-line pt-4">
                <button
                  onClick={() => {
                    setDeletingMaterialId(String(viewingMaterial.id))
                  }}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-danger hover:underline"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>Delete Material</span>
                </button>

                <button
                  onClick={() => setViewingMaterial(null)}
                  className="inline-flex h-9 items-center rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-soft hover:bg-brand/90"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* DELETE CONFIRMATION MODAL */}
        {deletingMaterialId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <div className="relative w-full max-w-sm rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 shadow-2xl text-ink dark:text-white space-y-4 text-center">
              <div className="grid h-12 w-12 place-items-center rounded-2xl bg-danger/10 text-danger mx-auto">
                <Trash2 className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-extrabold text-ink dark:text-white">Remove this material?</h3>
              <p className="text-xs text-muted dark:text-slate-300 font-bold leading-relaxed">
                This material will be removed from your course knowledge base.
              </p>

              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setDeletingMaterialId(null)}
                  className="h-10 rounded-xl border border-line bg-canvas px-5 text-xs font-bold text-muted hover:text-ink"
                >
                  Cancel
                </button>
                <button
                  onClick={() => deleteMutation.mutate(deletingMaterialId)}
                  disabled={deleteMutation.isPending}
                  className="h-10 rounded-xl bg-danger px-6 text-xs font-bold text-white shadow-soft hover:bg-danger/90 disabled:opacity-60"
                >
                  {deleteMutation.isPending ? 'Removing…' : 'Confirm Delete'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* UPLOAD MATERIAL MODAL */}
        {isUploadOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md">
            <div className="relative w-full max-w-lg rounded-3xl border border-line bg-surface dark:bg-slate-900 p-6 sm:p-8 shadow-2xl text-ink dark:text-white space-y-6">
              
              {/* Header */}
              <div className="flex items-center justify-between border-b border-line pb-4">
                <div>
                  <span className="text-xs font-mono font-bold text-brand uppercase">KNOWLEDGE INGESTION</span>
                  <h2 className="text-xl font-extrabold text-ink dark:text-white">Upload Material</h2>
                </div>
                <button
                  onClick={() => setIsUploadOpen(false)}
                  className="rounded-xl border border-line p-2 text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <p className="text-xs text-muted dark:text-slate-300 font-bold leading-relaxed">
                Select your notes, textbook, syllabus, or reference file.
              </p>

              <form onSubmit={handleUpload} className="space-y-4">
                {/* Title */}
                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    Material Title <span className="text-danger">*</span>
                  </label>
                  <input
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Unit 2 Lecture Notes / Textbook Reference"
                    className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-medium text-ink dark:text-white outline-none focus:border-brand"
                  />
                </div>

                {/* Document Type */}
                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    Document Type <span className="text-danger">*</span>
                  </label>
                  <select
                    value={docType}
                    onChange={(e) => setDocType(e.target.value as any)}
                    className="h-11 w-full rounded-xl border border-line bg-canvas px-3.5 text-sm font-bold text-ink dark:text-white outline-none focus:border-brand"
                  >
                    <option value="FACULTY_NOTES">Faculty Lecture Notes</option>
                    <option value="REFERENCE_BOOK">Reference Book / Textbook PDF</option>
                    <option value="PPT">Presentation Slides (PPT/PPTX)</option>
                    <option value="LAB_MANUAL">Lab Manual</option>
                    <option value="ASSIGNMENT">Assignment / Solution Guide</option>
                    <option value="QUESTION_BANK">Question Bank</option>
                  </select>
                </div>

                {/* File Dropzone */}
                <div>
                  <label className="block text-xs font-bold text-ink dark:text-white mb-1">
                    File <span className="text-danger">*</span>
                  </label>
                  <div className="rounded-2xl border border-dashed border-line bg-canvas p-6 text-center">
                    <input
                      required
                      type="file"
                      accept=".pdf,.docx,.txt,.ppt,.pptx"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className="hidden"
                      id="material-file-input"
                    />
                    <label htmlFor="material-file-input" className="cursor-pointer space-y-2 block">
                      <Upload className="h-8 w-8 text-brand mx-auto" />
                      {file ? (
                        <span className="text-xs font-bold text-teal-400 block truncate">
                          ✓ {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      ) : (
                        <span className="text-xs font-bold text-muted dark:text-slate-300 block">
                          Drop files here or browse (PDF, DOCX, TXT, PPT)
                        </span>
                      )}
                    </label>
                  </div>
                </div>

                {/* Errors */}
                {(clientError || uploadMutation.error) && (
                  <div className="rounded-xl border border-danger/20 bg-danger/10 p-3 text-xs font-bold text-danger">
                    {clientError || friendlyError(uploadMutation.error)}
                  </div>
                )}

                {/* Buttons */}
                <div className="pt-2 flex items-center justify-end gap-3 border-t border-line">
                  <button
                    type="button"
                    onClick={() => setIsUploadOpen(false)}
                    className="h-11 rounded-xl border border-line bg-canvas px-5 text-xs font-bold text-muted dark:text-slate-300 hover:text-ink dark:hover:text-white transition"
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
                        <span>Uploading & Processing…</span>
                      </>
                    ) : (
                      <span>Upload Material</span>
                    )}
                  </button>
                </div>

              </form>

            </div>
          </div>
        )}

      </div>
    </PageLayout>
  )
}
