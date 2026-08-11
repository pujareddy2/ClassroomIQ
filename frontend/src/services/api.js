/**
 * ClassroomIQ API Client for Multimedia & Lecture Capture
 */

const API_BASE = '/api/v1';

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.message || data?.error?.code || response.statusText || 'API request failed';
    throw new Error(errorMsg);
  }

  return data?.data ?? data;
}

export const api = {
  // Health
  checkHealth: async () => {
    const res = await fetch('/health');
    return res.json();
  },

  // Live Session
  startLiveSession: async ({
    course_name_or_code = 'CS101',
    faculty_name = 'Dr. Alan Turing',
    title = 'Classroom Lecture',
    classroom = 'Room 101',
    consent_confirmed = true,
    has_screen_share = false,
  }) => {
    return request(`${API_BASE}/multimedia/session/start`, {
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
    });
  },

  uploadLiveChunk: async (sessionId, chunkIndex, chunkBlob) => {
    const formData = new FormData();
    formData.append('chunk_index', chunkIndex);
    formData.append('chunk', chunkBlob, `chunk_${chunkIndex}.part`);

    return request(`${API_BASE}/multimedia/session/${sessionId}/chunk`, {
      method: 'POST',
      body: formData,
    });
  },

  completeLiveSession: async (sessionId, { duration_seconds = null, notes = null } = {}) => {
    return request(`${API_BASE}/multimedia/session/${sessionId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ duration_seconds, notes }),
    });
  },

  // Batch Upload
  uploadLecturePackage: async (formData) => {
    return request(`${API_BASE}/multimedia/upload`, {
      method: 'POST',
      body: formData,
    });
  },

  // Query Sessions
  listSessions: async (skip = 0, limit = 50) => {
    return request(`${API_BASE}/multimedia/sessions?skip=${skip}&limit=${limit}`);
  },

  getSessionDetail: async (sessionId) => {
    return request(`${API_BASE}/multimedia/session/${sessionId}`);
  },

  deleteSession: async (sessionId) => {
    return request(`${API_BASE}/multimedia/session/${sessionId}`, {
      method: 'DELETE',
    });
  },

  // Media Stream URLs
  getStreamUrl: (sessionId, mediaType = 'video') => {
    return `${API_BASE}/multimedia/session/${sessionId}/stream?media_type=${mediaType}`;
  },

  getSlideUrl: (sessionId, filename) => {
    return `${API_BASE}/multimedia/session/${sessionId}/slides/${filename}`;
  },
};

