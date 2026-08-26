import { api, unwrap } from './api/client'

export const lectureService = {
  list: async (courseId?: string) => unwrap<unknown[]>(await api.get('/lecture/list', { params: { course_id: courseId } })),
  upload: async (payload: FormData) => unwrap<Record<string, unknown>>(await api.post('/lecture/upload', payload)),
  get: async (id: string) => unwrap<Record<string, unknown>>(await api.get(`/lecture/${id}`)),
  status: async (id: string) => unwrap<Record<string, unknown>>(await api.get(`/lecture/${id}/status`)),
  chunks: async (id: string) => unwrap<unknown[]>(await api.get(`/lecture/${id}/chunks`)),
  statistics: async (id: string) => unwrap<Record<string, unknown>>(await api.get(`/lecture/${id}/statistics`)),
  delete: async (id: string) => unwrap<Record<string, unknown>>(await api.delete(`/lecture/${id}`)),
}
