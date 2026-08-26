import { useQuery, type UseQueryOptions } from '@tanstack/react-query'
import axios from 'axios'

export const friendlyError = (error: unknown) => { if (!axios.isAxiosError(error)) return 'Unable to complete this request. Please try again.'; const status = error.response?.status; if (status === 401) return 'Your session has expired. Please sign in again.'; if (status === 403) return 'You do not have permission to view this information.'; if (status === 404) return 'This resource was not found.'; if (status === 422) return 'Please check the submitted information.'; return error.response?.data?.message ?? 'The service is currently unavailable.' }
export const shouldRetry = (count: number, error: unknown) => !axios.isAxiosError(error) || (error.response?.status ?? 500) >= 500 ? count < 2 : false
export function useApiQuery<T>(key: readonly unknown[], fn: () => Promise<T>, enabled = true, options?: Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn' | 'enabled'>) { return useQuery({ queryKey: key, queryFn: fn, enabled, retry: shouldRetry, ...options }) }
