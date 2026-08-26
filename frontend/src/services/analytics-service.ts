export const analyticsService = { unavailable: async (): Promise<never> => Promise.reject(new Error('Analytics endpoints are not available in the current FastAPI API.')) }
