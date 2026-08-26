import { api, unwrap } from './api/client'
export const assistantService = { ask: async (lectureId: string, question: string) => unwrap<{ answer: string }>(await api.post('/assistant/ask', { lecture_id: lectureId, question })) }
