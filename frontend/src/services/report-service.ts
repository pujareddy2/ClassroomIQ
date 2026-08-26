export const reportService = { unavailable: async (): Promise<never> => Promise.reject(new Error('Report endpoints are not available in the current FastAPI API.')) }
