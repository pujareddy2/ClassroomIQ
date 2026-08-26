export type ApiMetadata = { timestamp: string; execution_time: number; request_id: string; api_version: string }
export type ApiResponse<T> = { status: 'SUCCESS'; message: string; data: T; metadata: ApiMetadata }
export type ApiError = { status: 'ERROR'; message: string; error: { code: string; details: unknown[] }; metadata: ApiMetadata }
export type NotificationItem = { id: string; title: string; body: string; category: 'System' | 'Lecture' | 'Coverage' | 'Validation' | 'Recommendations' | 'Reports'; priority: 'info' | 'warning' | 'danger'; createdAt: string; read: boolean }
