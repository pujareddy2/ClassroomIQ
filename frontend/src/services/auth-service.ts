import { api, unwrap } from './api/client'
import type { CurrentUser } from '@/store/auth-store'

type LoginResponse = { access_token: string; token_type: string; user: CurrentUser }
export const authService = { login: async (payload: { email: string; password: string }) => unwrap<LoginResponse>(await api.post('/auth/login', payload)), register: async (payload: Record<string, unknown>) => unwrap<CurrentUser>(await api.post('/auth/register', payload)), me: async () => unwrap<CurrentUser>(await api.get('/auth/me')) }
