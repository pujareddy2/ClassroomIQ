import { useEffect, useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useApiQuery } from './use-api-query'
import { useContextStore } from '@/store/context-store'
import { workflowService } from '@/services/workflow-service'

const MAX_WAIT_MS = 120_000

export function useLectureAnalysis() {
  const { selectedLectureId, selectedCurriculumId } = useContextStore()
  const client = useQueryClient(); const startedFor = useRef<string | null>(null); const [timedOut, setTimedOut] = useState(false)
  const ready = Boolean(selectedLectureId && selectedCurriculumId); const key = ready ? `${selectedLectureId}:${selectedCurriculumId}` : null
  const status = useApiQuery(['analysis-status', selectedLectureId], () => workflowService.status(selectedLectureId!), ready, { retry: false, refetchInterval: (query) => ['PENDING', 'PROCESSING'].includes(query.state.data?.overall_status ?? '') ? 2000 : false })
  const run = useMutation({ mutationFn: () => workflowService.run({ lecture_id: selectedLectureId!, curriculum_id: selectedCurriculumId! }), onSuccess: () => client.invalidateQueries({ queryKey: ['analysis-status', selectedLectureId] }) })
  useEffect(() => { setTimedOut(false); startedFor.current = null }, [key])
  useEffect(() => { if (ready && status.data?.overall_status === 'NOT_STARTED' && startedFor.current !== key && !run.isPending) { startedFor.current = key; run.mutate() } }, [key, ready, run, status.data?.overall_status])
  useEffect(() => { if (!status.data?.started_at || !['PENDING', 'PROCESSING'].includes(status.data.overall_status)) return; const remaining = Math.max(0, MAX_WAIT_MS - (Date.now() - new Date(status.data.started_at).getTime())); const timer = window.setTimeout(() => setTimedOut(true), remaining); return () => window.clearTimeout(timer) }, [status.data?.overall_status, status.data?.started_at])
  const retry = () => { startedFor.current = null; setTimedOut(false); run.mutate() }
  return { status: status.data, isChecking: status.isLoading || run.isPending, isCompleted: status.data?.overall_status === 'COMPLETED', isFailed: status.data?.overall_status === 'FAILED' || run.isError, timedOut, error: run.error ?? status.error, retry, refresh: status.refetch, ready }
}
