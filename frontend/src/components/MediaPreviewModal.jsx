import React, { useState, useEffect, useRef } from 'react';
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
  MessageSquare,
  Video,
  Share2,
} from 'lucide-react';
import { api } from '../services/api';
import TranscriptViewer from './TranscriptViewer';
import VisualTimelineViewer from './VisualTimelineViewer';
import LectureStructureViewer from './LectureStructureViewer';
import HandoverContractModal from './HandoverContractModal';

export default function MediaPreviewModal({ session, onClose, onDelete }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [activeTab, setActiveTab] = useState('structure'); // 'structure' | 'visual' | 'transcript' | 'slides'
  const [showHandoverModal, setShowHandoverModal] = useState(false);

  const videoRef = useRef(null);
  const audioRef = useRef(null);

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

  const handleSeekToTimestamp = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(() => null);
    } else if (audioRef.current) {
      audioRef.current.currentTime = seconds;
      audioRef.current.play().catch(() => null);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(5, 8, 15, 0.88)',
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
          width: '1100px',
          maxWidth: '96vw',
          maxHeight: '92vh',
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
            <button
              className="btn btn-secondary"
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
              onClick={() => setShowHandoverModal(true)}
              title="View Member 1 Handover Contract for Member 2"
            >
              <Share2 size={14} color="var(--accent-primary)" /> Member 2 Handover
            </button>

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

        {/* Handover Contract Modal */}
        {showHandoverModal && (
          <HandoverContractModal
            sessionId={session.session_id}
            onClose={() => setShowHandoverModal(false)}
          />
        )}


        {/* Top Media Player */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>
          {/* Media Player Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Lecture Media Stream</h4>
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
                  ref={videoRef}
                  controls
                  style={{ width: '100%', maxHeight: '300px' }}
                  src={api.getStreamUrl(session.session_id, 'video')}
                />
              ) : session.has_audio ? (
                <div style={{ padding: '2rem', textAlign: 'center', width: '100%' }}>
                  <Volume2 size={40} color="var(--accent-primary)" style={{ margin: '0 auto 1rem' }} />
                  <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>Audio Lecture Recording</p>
                  <audio ref={audioRef} controls style={{ width: '100%' }} src={api.getStreamUrl(session.session_id, 'audio_16k')} />
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>No media file available</p>
              )}
            </div>

            {/* Technical Specs Summary */}
            <div style={{ background: 'var(--bg-tertiary)', padding: '0.85rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', fontSize: '0.78rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem' }}>
              <div>Format: <strong style={{ color: 'var(--text-primary)' }}>{meta?.format || 'webm/wav'}</strong></div>
              <div>Duration: <strong style={{ color: 'var(--text-primary)' }}>{meta?.duration_seconds ? `${Math.round(meta.duration_seconds)}s` : 'N/A'}</strong></div>
              <div>Sample Rate: <strong style={{ color: 'var(--text-primary)' }}>16,000 Hz (Mono WAV)</strong></div>
              <div>Whisper Ready: <strong style={{ color: 'var(--accent-emerald)' }}>✓ Normalized</strong></div>
            </div>
          </div>

          {/* Right Column: Tab View (Structure vs Visual Timeline vs Transcript vs Slides) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {/* Tab Header */}
            <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-tertiary)', padding: '0.3rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <button
                className="btn"
                style={{
                  flex: 1,
                  padding: '0.4rem',
                  fontSize: '0.82rem',
                  background: activeTab === 'structure' ? 'linear-gradient(135deg, var(--accent-primary) 0%, #a855f7 100%)' : 'transparent',
                  color: activeTab === 'structure' ? '#ffffff' : 'var(--text-secondary)',
                }}
                onClick={() => setActiveTab('structure')}
              >
                <Layers size={14} /> Structure & Sync
              </button>

              <button
                className="btn"
                style={{
                  flex: 1,
                  padding: '0.4rem',
                  fontSize: '0.82rem',
                  background: activeTab === 'visual' ? 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)' : 'transparent',
                  color: activeTab === 'visual' ? '#ffffff' : 'var(--text-secondary)',
                }}
                onClick={() => setActiveTab('visual')}
              >
                <Video size={14} /> Video
              </button>

              <button
                className="btn"
                style={{
                  flex: 1,
                  padding: '0.4rem',
                  fontSize: '0.82rem',
                  background: activeTab === 'transcript' ? 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)' : 'transparent',
                  color: activeTab === 'transcript' ? '#ffffff' : 'var(--text-secondary)',
                }}
                onClick={() => setActiveTab('transcript')}
              >
                <MessageSquare size={14} /> Speech
              </button>

              {slides.length > 0 && (
                <button
                  className="btn"
                  style={{
                    flex: 1,
                    padding: '0.4rem',
                    fontSize: '0.82rem',
                    background: activeTab === 'slides' ? 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)' : 'transparent',
                    color: activeTab === 'slides' ? '#ffffff' : 'var(--text-secondary)',
                  }}
                  onClick={() => setActiveTab('slides')}
                >
                  <FileText size={14} /> Slides ({slides.length})
                </button>
              )}
            </div>

            {/* Tab Body */}
            {activeTab === 'structure' ? (
              <LectureStructureViewer sessionId={session.session_id} onSeekToTimestamp={handleSeekToTimestamp} />
            ) : activeTab === 'visual' ? (
              <VisualTimelineViewer sessionId={session.session_id} onSeekToTimestamp={handleSeekToTimestamp} />
            ) : activeTab === 'transcript' ? (
              <TranscriptViewer sessionId={session.session_id} onSeekToTimestamp={handleSeekToTimestamp} />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
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
                    height: '350px',
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
        </div>
      </div>
    </div>
  );
}
