/**
 * ClassroomIQ API Client
 * Handles auth headers, async job polling, and all Multimedia/Audio/Video/Structuring API calls.
 */

const API_BASE = '/api/v1';

// ── Auth Token Helpers ─────────────────────────────────────────────────────────

function getStoredToken() {
  const directToken = localStorage.getItem('token') || localStorage.getItem('classroomiq_token') || sessionStorage.getItem('classroomiq_token');
  if (directToken) return directToken;
  try {
    const authStore = JSON.parse(localStorage.getItem('auth-storage') || '{}');
    return authStore?.state?.token || null;
  } catch {
    return null;
  }
}

export function setAuthToken(token) {
  localStorage.setItem('classroomiq_token', token);
}

export function clearAuthToken() {
  localStorage.removeItem('classroomiq_token');
  sessionStorage.removeItem('classroomiq_token');
}

function getAuthHeaders() {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Base Request Helper ────────────────────────────────────────────────────────

async function request(url, options = {}) {
  // Merge auth headers into every request automatically
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    // Surface a clean error message
    const errorMsg =
      data?.detail ||
      data?.message ||
      data?.error?.code ||
      response.statusText ||
      'API request failed';

    // Clear stale token on 401 so the user is redirected to login
    if (response.status === 401) {
      clearAuthToken();
    }
    throw new Error(errorMsg);
  }

  return data?.data ?? data;
}

// ── API Client ─────────────────────────────────────────────────────────────────

export const api = {

  // ── Auth ──────────────────────────────────────────────────────────────────
  register: async ({ email, password, full_name }) =>
    request(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: async ({ email, password }) => {
    const res = await request(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (res?.access_token) setAuthToken(res.access_token);
    return res;
  },

  logout: () => clearAuthToken(),

  getMe: async () => request(`${API_BASE}/auth/me`),

  // ── Health ────────────────────────────────────────────────────────────────
  checkHealth: async () => {
    const res = await fetch('/health');
    return res.json();
  },

  // ── Live Session ──────────────────────────────────────────────────────────
  startLiveSession: async ({
    course_name_or_code = 'CS101',
    faculty_name = 'Dr. Alan Turing',
    title = 'Classroom Lecture',
    classroom = 'Room 101',
    consent_confirmed = true,
    has_screen_share = false,
  }) =>
    request(`${API_BASE}/multimedia/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        course_name_or_code,
        faculty_name,
        title,
        classroom,
        consent_confirmed,
        has_screen_share,
      }),
    }),

  uploadLiveChunk: async (sessionId, chunkIndex, chunkBlob) => {
    const formData = new FormData();
    formData.append('chunk_index', chunkIndex);
    formData.append('chunk', chunkBlob, `chunk_${chunkIndex}.part`);
    return request(`${API_BASE}/multimedia/session/${sessionId}/chunk`, {
      method: 'POST',
      body: formData,
    });
  },

  completeLiveSession: async (sessionId, { duration_seconds = null, notes = null } = {}) =>
    request(`${API_BASE}/multimedia/session/${sessionId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ duration_seconds, notes }),
    }),

  // ── Batch Upload ──────────────────────────────────────────────────────────
  uploadLecturePackage: async (formData) =>
    request(`${API_BASE}/multimedia/upload`, { method: 'POST', body: formData }),

  // ── Query Sessions ────────────────────────────────────────────────────────
  listSessions: async (skip = 0, limit = 50) =>
    request(`${API_BASE}/multimedia/sessions?skip=${skip}&limit=${limit}`),

  getSessionDetail: async (sessionId) =>
    request(`${API_BASE}/multimedia/session/${sessionId}`),

  deleteSession: async (sessionId) =>
    request(`${API_BASE}/multimedia/session/${sessionId}`, { method: 'DELETE' }),

  // ── Media Stream URLs (no auth needed — these are direct file references) ─
  getStreamUrl: (sessionId, mediaType = 'video') =>
    `${API_BASE}/multimedia/session/${sessionId}/stream?media_type=${mediaType}`,

  getSlideUrl: (sessionId, filename) =>
    `${API_BASE}/multimedia/session/${sessionId}/slides/${filename}`,

  // ── Async Job Queue ───────────────────────────────────────────────────────

  /**
   * Submit audio processing — returns job_id immediately.
   * Poll api.getJobStatus(jobId) for progress.
   */
  processAudio: async (sessionId, options = {}) =>
    request(`${API_BASE}/audio/session/${sessionId}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    }),

  /** Get transcript (call after job status is COMPLETED) */
  getTranscript: async (sessionId) =>
    request(`${API_BASE}/audio/session/${sessionId}/transcript`),

  /** Get the latest audio job status for a session (convenience) */
  getAudioJobStatus: async (sessionId) =>
    request(`${API_BASE}/audio/session/${sessionId}/job-status`),

  /**
   * Submit video processing — returns job_id immediately.
   */
  processVideo: async (sessionId, options = {}) =>
    request(`${API_BASE}/video/process/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    }),

  /**
   * Submit full audio + video pipeline as a single job.
   */
  processFullPipeline: async (sessionId) =>
    request(`${API_BASE}/video/process-full/${sessionId}`, { method: 'POST' }),

  getVideoTimeline: async (sessionId) =>
    request(`${API_BASE}/video/timeline/${sessionId}`),

  getVideoSummary: async (sessionId) =>
    request(`${API_BASE}/video/summary/${sessionId}`),

  getKeyframeUrl: (sessionId, filename) =>
    `${API_BASE}/video/keyframe/${sessionId}/${filename}`,

  analyzeVideoFile: async (formData) =>
    request(`${API_BASE}/video/analyze-file`, { method: 'POST', body: formData }),

  // ── Job Status Polling ────────────────────────────────────────────────────
  getJobStatus: async (jobId) =>
    request(`${API_BASE}/jobs/${jobId}`),

  getSessionJobs: async (sessionId) =>
    request(`${API_BASE}/jobs/session/${sessionId}`),

  /**
   * Poll a job until COMPLETED or FAILED. Returns the final job status.
   * @param {string} jobId - The job UUID to poll
   * @param {function} onProgress - Called with (progress: 0–100, status: string) each poll
   * @param {number} intervalMs - Poll interval in milliseconds (default: 3000)
   * @param {number} timeoutMs - Max wait time in milliseconds (default: 900000 = 15min)
   */
  pollJobUntilDone: async (jobId, onProgress = null, intervalMs = 3000, timeoutMs = 900000) => {
    const startTime = Date.now();
    while (Date.now() - startTime < timeoutMs) {
      const jobStatus = await request(`${API_BASE}/jobs/${jobId}`);
      if (onProgress) onProgress(jobStatus.progress || 0, jobStatus.status);
      if (jobStatus.status === 'COMPLETED' || jobStatus.status === 'FAILED') {
        return jobStatus;
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
    throw new Error(`Job ${jobId} timed out after ${timeoutMs / 1000}s`);
  },

  // ── Lecture Structuring & Handover ────────────────────────────────────────
  processLectureStructuring: async (sessionId, options = {}) =>
    request(`${API_BASE}/structuring/process/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    }),

  getStructuredLecture: async (sessionId) =>
    request(`${API_BASE}/structuring/structured-lecture/${sessionId}`),

  getSyncTimeline: async (sessionId) =>
    request(`${API_BASE}/structuring/sync-timeline/${sessionId}`),

  getTopicSegments: async (sessionId) =>
    request(`${API_BASE}/structuring/topic-segments/${sessionId}`),

  // ── Handover Contract ─────────────────────────────────────────────────────
  getHandoverContract: async (sessionId) =>
    request(`${API_BASE}/multimedia/handover-contract/${sessionId}`),
};
