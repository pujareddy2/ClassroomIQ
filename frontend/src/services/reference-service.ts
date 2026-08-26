import { api, unwrap } from './api/client'

export const referenceService = {
  upload: async (payload: FormData) => unwrap<Record<string, unknown>>(await api.post('/reference/upload', payload)),
  list: async (courseId?: string) => unwrap<unknown[]>(await api.get('/reference/list', { params: { course_id: courseId } })),
  delete: async (id: string) => unwrap<Record<string, unknown>>(await api.delete(`/reference/${id}`)),
}
