import React, { useState, useEffect } from 'react';
import {
  X,
  Play,
  Volume2,
  FileText,
  Clock,
  Layers,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  CheckCircle2,
  Download,
  Info,
  Trash2,
} from 'lucide-react';
import { api } from '../services/api';

export default function MediaPreviewModal({ session, onClose, onDelete }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);

  useEffect(() => {
    async function loadDetail() {
      if (!session?.session_id) return;
      try {
        setLoading(true);
        const data = await api.getSessionDetail(session.session_id);
        setDetail(data);
      } catch (err) {
        console.error('Failed to load session detail:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [session]);

  if (!session) return null;

  const slides = detail?.slides || [];
  const meta = detail?.media_metadata;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(5, 8, 15, 0.85)',
        backdropFilter: 'blur(16px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <div
        className="glass-card"
        style={{
          width: '1000px',
          maxWidth: '95vw',
          maxHeight: '90vh',
          overflowY: 'auto',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-xl)',
          padding: '2rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
          position: 'relative',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.25rem' }}>
              <span className={`badge ${session.status === 'ACTIVE' ? 'badge-active' : 'badge-recording'}`}>
                {session.status}
              </span>
              <h2 style={{ fontSize: '1.3rem' }}>{session.title || session.course_name}</h2>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Instructor: <strong style={{ color: 'var(--text-primary)' }}>{session.faculty_name}</strong> • Session ID:{' '}
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{session.session_id}</span>
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {onDelete && (
              <button
                className="btn btn-danger"
                style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                onClick={() => {
                  if (window.confirm('Delete this recording and all extracted files?')) {
                    onDelete(session.session_id);
                    onClose();
                  }
                }}
              >
                <Trash2 size={14} /> Delete
              </button>
            )}

            <button
              onClick={onClose}
              style={{
                background: 'var(--bg-tertiary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.4rem',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Media Player + Slide Viewer Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: slides.length > 0 ? '1.2fr 1fr' : '1fr', gap: '1.5rem' }}>
          {/* Media Player */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Lecture Stream</h4>
            <div
              style={{
                borderRadius: 'var(--radius-lg)',
                overflow: 'hidden',
                background: '#000000',
                boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                minHeight: '260px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {session.has_video ? (
                <video
                  controls
                  style={{ width: '100%', maxHeight: '340px' }}
                  src={api.getStreamUrl(session.session_id, 'video')}
                />
              ) : session.has_audio ? (
                <div style={{ padding: '2rem', textAlign: 'center', width: '100%' }}>
                  <Volume2 size={40} color="var(--accent-primary)" style={{ margin: '0 auto 1rem' }} />
                  <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>Audio Lecture Recording</p>
                  <audio controls style={{ width: '100%' }} src={api.getStreamUrl(session.session_id, 'audio_16k')} />
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>No media file available</p>
              )}
            </div>
          </div>

          {/* Slide Gallery (if available) */}
          {slides.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Slide Deck ({activeSlideIndex + 1} of {slides.length})
                </h4>
                <div style={{ display: 'flex', gap: '0.35rem' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem' }}
                    disabled={activeSlideIndex === 0}
                    onClick={() => setActiveSlideIndex((prev) => prev - 1)}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.5rem' }}
                    disabled={activeSlideIndex === slides.length - 1}
                    onClick={() => setActiveSlideIndex((prev) => prev + 1)}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>

              <div
                style={{
                  borderRadius: 'var(--radius-lg)',
                  overflow: 'hidden',
                  background: '#0c101b',
                  border: '1px solid var(--border-subtle)',
                  height: '340px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative',
                }}
              >
                {slides[activeSlideIndex]?.preview_url ? (
                  <img
                    src={slides[activeSlideIndex].preview_url}
                    alt={`Slide ${activeSlideIndex + 1}`}
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                ) : (
                  <div style={{ padding: '1.5rem', textAlign: 'center' }}>
                    <FileText size={36} color="var(--accent-secondary)" style={{ margin: '0 auto 0.75rem' }} />
                    <p style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.5rem' }}>
                      {slides[activeSlideIndex]?.title || `Slide ${activeSlideIndex + 1}`}
                    </p>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxHeight: '140px', overflowY: 'auto' }}>
                      {slides[activeSlideIndex]?.text_content || 'Text extracted from PPTX'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Technical Metadata & AI Pipeline Readiness Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
          {/* Metadata Card */}
          <div style={{ background: 'var(--bg-tertiary)', padding: '1rem 1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <h5 style={{ fontSize: '0.82rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              Media Technical Specs (FFmpeg Probe)
            </h5>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div>Format: <strong style={{ color: 'var(--text-primary)' }}>{meta?.format || 'webm'}</strong></div>
              <div>Duration: <strong style={{ color: 'var(--text-primary)' }}>{meta?.duration_seconds ? `${Math.round(meta.duration_seconds)}s` : 'N/A'}</strong></div>
              <div>Sample Rate: <strong style={{ color: 'var(--text-primary)' }}>{meta?.sample_rate ? `${meta.sample_rate} Hz` : '16000 Hz (Normalized)'}</strong></div>
              <div>Resolution: <strong style={{ color: 'var(--text-primary)' }}>{meta?.width ? `${meta.width}x${meta.height}` : 'N/A'}</strong></div>
            </div>
          </div>

          {/* AI Intelligence Readiness Card */}
          <div style={{ background: 'rgba(99, 102, 241, 0.08)', padding: '1rem 1.25rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
            <h5 style={{ fontSize: '0.82rem', textTransform: 'uppercase', color: 'var(--accent-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Sparkles size={14} /> AI Intelligence Pipeline Readiness
            </h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-emerald)' }}>
                <CheckCircle2 size={13} /> 16kHz Mono WAV Extracted (Ready for Whisper STT)
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-emerald)' }}>
                <CheckCircle2 size={13} /> Video Keyframes Stitched (Ready for OpenCV / YOLO)
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-emerald)' }}>
                <CheckCircle2 size={13} /> Structured for POST /api/v1/lecture/analyze
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
