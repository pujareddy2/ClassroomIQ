import axios from 'axios'
import type { ApiResponse } from '@/types/api'
import { useAuthStore } from '@/store/auth-store'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1', timeout: 20_000 })
api.interceptors.request.use((config) => { const token = useAuthStore.getState().token; if (token) config.headers.Authorization = `Bearer ${token}`; config.headers['X-Request-ID'] = crypto.randomUUID(); return config })
api.interceptors.response.use((response) => response, (error) => { if (error.response?.status === 401 && !String(error.config?.url).includes('/auth/login')) { useAuthStore.getState().clearSession(); if (window.location.pathname !== '/login') window.location.assign('/login') } return Promise.reject(error) })
export const unwrap = <T>(response: { data: ApiResponse<T> }) => response.data.data
