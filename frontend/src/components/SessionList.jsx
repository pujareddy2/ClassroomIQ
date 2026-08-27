import React, { useState, useEffect } from 'react';
import {
  Film,
  RefreshCw,
  Play,
  FileVideo,
  FileAudio,
  FileText,
  Clock,
  User,
  MapPin,
  Calendar,
  Search,
  CheckCircle2,
  Radio,
  Trash2,
  AlertTriangle,
  Share2,
} from 'lucide-react';
import { api } from '../services/api';
import MediaPreviewModal from './MediaPreviewModal';
import HandoverContractModal from './HandoverContractModal';

export default function SessionList() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSession, setSelectedSession] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [deleteConfirmSession, setDeleteConfirmSession] = useState(null);
  const [handoverSessionId, setHandoverSessionId] = useState(null);


  const fetchSessions = async () => {
    try {
      setLoading(true);
      const res = await api.listSessions();
      setSessions(res?.items || []);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleDeleteSession = async (sessionId, e) => {
    if (e) e.stopPropagation();
    try {
      setDeletingId(sessionId);
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (selectedSession?.session_id === sessionId) {
        setSelectedSession(null);
      }
      setDeleteConfirmSession(null);
    } catch (err) {
      alert(`Failed to delete session: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm(`Are you sure you want to delete all ${sessions.length} sessions?`)) return;
    try {
      setLoading(true);
      for (const s of sessions) {
        await api.deleteSession(s.session_id).catch(() => null);
      }
      setSessions([]);
      setSelectedSession(null);
    } catch (err) {
      alert('Error clearing sessions');
    } finally {
      setLoading(false);
    }
  };

  const filteredSessions = sessions.filter((s) => {
    const query = searchQuery.toLowerCase();
    return (
      (s.course_name && s.course_name.toLowerCase().includes(query)) ||
      (s.faculty_name && s.faculty_name.toLowerCase().includes(query)) ||
      (s.title && s.title.toLowerCase().includes(query))
    );
  });

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.round(seconds / 60);
    return `${mins} min`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem' }}>Recorded & Uploaded Sessions</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            List of all captured lectures with extracted 16kHz audio tracks, video keyframes, and slide decks.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Search Input */}
          <div style={{ position: 'relative', width: '240px' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              className="form-input"
              style={{ paddingLeft: '2.5rem', fontSize: '0.85rem' }}
              placeholder="Search course or faculty..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <button className="btn btn-secondary" onClick={fetchSessions} disabled={loading} style={{ padding: '0.65rem 0.9rem' }}>
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>

          {sessions.length > 0 && (
            <button className="btn btn-danger" onClick={handleClearAll} style={{ padding: '0.65rem 0.9rem', fontSize: '0.82rem' }}>
              <Trash2 size={15} />
              Clear All ({sessions.length})
            </button>
          )}
        </div>
      </div>

      {/* Sessions Grid */}
      {loading && sessions.length === 0 ? (
        <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
          <p>Loading captured lecture sessions...</p>
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="glass-card" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
          <Film size={40} color="var(--text-muted)" style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.35rem' }}>No Lecture Sessions Found</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            Start a live recording session or upload a lecture package to see it here.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.5rem' }}>
          {filteredSessions.map((session) => (
            <div
              key={session.session_id}
              className="glass-card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '1.25rem',
                cursor: 'pointer',
                position: 'relative',
              }}
              onClick={() => setSelectedSession(session)}
            >
              <div>
                {/* Status & Date & Delete Trigger */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span className={`badge ${session.status === 'ACTIVE' ? 'badge-active' : 'badge-recording'}`}>
                    {session.status === 'RECORDING' && <Radio size={12} />}
                    {session.status}
                  </span>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Calendar size={12} />
                      {new Date(session.created_at).toLocaleDateString()}
                    </span>

                    {/* Quick Delete Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteConfirmSession(session);
                      }}
                      title="Delete this recording"
                      style={{
                        background: 'rgba(244, 63, 94, 0.1)',
                        border: '1px solid rgba(244, 63, 94, 0.25)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '0.3rem',
                        color: 'var(--accent-rose)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                {/* Course & Title */}
                <h3 style={{ fontSize: '1.1rem', marginBottom: '0.35rem', lineHeight: 1.3 }}>
                  {session.title || session.course_name}
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--accent-primary)', fontWeight: 600, marginBottom: '0.75rem' }}>
                  {session.course_name}
                </p>

                {/* Metadata List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <User size={13} color="var(--text-muted)" />
                    <span>{session.faculty_name}</span>
                  </div>
                  {session.classroom && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <MapPin size={13} color="var(--text-muted)" />
                      <span>{session.classroom}</span>
                    </div>
                  )}
                  {session.duration_seconds && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Clock size={13} color="var(--text-muted)" />
                      <span>{formatDuration(session.duration_seconds)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Badges & Action */}
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {session.has_video && (
                    <span style={{ padding: '0.2rem 0.45rem', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontSize: '0.7rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <FileVideo size={11} /> Video
                    </span>
                  )}
                  {session.has_audio && (
                    <span style={{ padding: '0.2rem 0.45rem', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontSize: '0.7rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <FileAudio size={11} /> 16kHz Audio
                    </span>
                  )}
                  {session.has_slides && (
                    <span style={{ padding: '0.2rem 0.45rem', borderRadius: '4px', background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', fontSize: '0.7rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <FileText size={11} /> {session.slide_count} Slides
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '0.4rem 0.65rem', fontSize: '0.75rem' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setHandoverSessionId(session.session_id);
                    }}
                    title="View Member 1 Handover Contract for Member 2"
                  >
                    <Share2 size={12} color="var(--accent-primary)" />
                    Handover
                  </button>

                  <button className="btn btn-primary" style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}>
                    <Play size={13} fill="currentColor" /> Inspect
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Handover Contract Modal */}
      {handoverSessionId && (
        <HandoverContractModal
          sessionId={handoverSessionId}
          onClose={() => setHandoverSessionId(null)}
        />
      )}


      {/* Delete Confirmation Dialog */}
      {deleteConfirmSession && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(5, 8, 15, 0.8)',
            backdropFilter: 'blur(8px)',
            zIndex: 150,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem',
          }}
          onClick={() => setDeleteConfirmSession(null)}
        >
          <div
            className="glass-card"
            style={{ maxWidth: '420px', width: '100%', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', padding: '1.75rem', textAlign: 'center' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(244, 63, 94, 0.15)', color: 'var(--accent-rose)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}>
              <AlertTriangle size={24} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Delete Lecture Session?</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', lineHeight: 1.4 }}>
              Are you sure you want to delete <strong style={{ color: 'var(--text-primary)' }}>{deleteConfirmSession.title || deleteConfirmSession.course_name}</strong>? This will remove all audio tracks, video files, and slide previews from disk.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <button className="btn btn-secondary" onClick={() => setDeleteConfirmSession(null)}>
                Cancel
              </button>
              <button
                className="btn btn-danger"
                disabled={deletingId === deleteConfirmSession.session_id}
                onClick={() => handleDeleteSession(deleteConfirmSession.session_id)}
              >
                <Trash2 size={15} />
                {deletingId === deleteConfirmSession.session_id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal View */}
      {selectedSession && (
        <MediaPreviewModal
          session={selectedSession}
          onClose={() => setSelectedSession(null)}
          onDelete={(id) => handleDeleteSession(id)}
        />
      )}
    </div>
  );
}
