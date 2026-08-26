import { type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useContextStore } from '@/store/context-store'

export function PageLayout({ 
  title, 
  description, 
  actions, 
  hideContextBadges = false,
  children 
}: { 
  title: string
  description: string
  actions?: ReactNode
  hideContextBadges?: boolean
  children: ReactNode 
}) { 
  const location = useLocation()
  const { selectedLectureId, selectedCourseId, selectedCourseName, semester } = useContextStore()
  const courseBadgeName = selectedCourseName || (selectedCourseId ? (selectedCourseId.length > 20 ? 'Active Course' : selectedCourseId) : 'Choose a curriculum')

  return (
    <div className="space-y-7">
      <div className="text-sm font-bold text-muted dark:text-slate-300">
        <Link to="/dashboard" className="hover:text-brand transition">Workspace</Link>
        <span className="px-2">/</span>
        <span className="text-ink dark:text-white capitalize">{location.pathname.split('/').filter(Boolean).at(-1) ?? 'dashboard'}</span>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-ink dark:text-white">{title}</h1>
          <p className="mt-2 max-w-2xl text-sm font-semibold text-muted dark:text-slate-200 leading-relaxed">{description}</p>
        </div>
        {actions}
      </div>

      {!hideContextBadges && (
        <div className="flex flex-wrap gap-2 text-xs font-mono font-bold">
          <span className="rounded-full bg-surface border border-line px-3 py-1 text-muted dark:text-slate-300">
            Course: {courseBadgeName}
          </span>
          <span className="rounded-full bg-surface border border-line px-3 py-1 text-muted dark:text-slate-300">
            Semester: {semester ?? 'Semester 6 (2026-2027)'}
          </span>
          {selectedLectureId && (
            <span className="rounded-full bg-brand-soft px-3 py-1 text-brand border border-brand/20">
              Active lecture selected
            </span>
          )}
        </div>
      )}

      {children}
    </div>
  )
}
