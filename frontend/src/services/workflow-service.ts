import { api, unwrap } from './api/client'

export type WorkflowStatus = { lecture_id: string; job_id: string | null; overall_status: 'NOT_STARTED' | 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'; validation_status: string; coverage_status: string; teaching_status: string; recommendation_status: string; explainability_status: string; progress_percentage: number; current_stage: string; estimated_remaining_seconds: number; started_at?: string; error_message: string | null }
export const workflowService = { status: async (lectureId: string) => unwrap<WorkflowStatus>(await api.get(`/analysis/status/${lectureId}`)), run: async (payload: { lecture_id: string; curriculum_id: string; regenerate?: boolean }) => unwrap<WorkflowStatus>(await api.post('/analysis/run', payload)) }
