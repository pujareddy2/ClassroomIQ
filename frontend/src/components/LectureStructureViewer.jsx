import React, { useState, useEffect } from 'react';
import {
  Layers,
  Sparkles,
  RefreshCw,
  Clock,
  BookOpen,
  Volume2,
  Video,
  Monitor,
  Edit3,
  User,
  Users,
  Play,
  CheckCircle2,
  Sliders,
  Download,
  Share2,
  ChevronRight,
  Gauge,
  Tag,
  Code,
  FileText,
} from 'lucide-react';
import { api } from '../services/api';

export default function LectureStructureViewer({ sessionId, onSeekToTimestamp }) {
  const [structuredData, setStructuredData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [hoveredTime, setHoveredTime] = useState(null);

  // Structuring Config
  const [minTopicDuration, setMinTopicDuration] = useState(15.0);
  const [syncResolution, setSyncResolution] = useState(2.0);

  const fetchStructuredLecture = async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const res = await api.getStructuredLecture(sessionId);
      setStructuredData(res);
      if (res.topic_segments && res.topic_segments.length > 0) {
        setSelectedTopic(res.topic_segments[0]);
      }
    } catch (err) {
      console.error('Failed to load structured lecture:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStructuredLecture();
  }, [sessionId]);

  const handleRunStructuring = async () => {
    try {
      setProcessing(true);
      const res = await api.processLectureStructuring(sessionId, {
        min_topic_duration_sec: parseFloat(minTopicDuration),
        sync_resolution_sec: parseFloat(syncResolution),
        auto_persist_db: true,
      });
      setStructuredData(res);
      if (res.topic_segments && res.topic_segments.length > 0) {
        setSelectedTopic(res.topic_segments[0]);
      }
    } catch (err) {
      alert(`Lecture Structuring pipeline failed: ${err.message}`);
    } finally {
      setProcessing(false);
    }
  };

  const formatTimestamp = (sec) => {
    if (isNaN(sec) || sec === null || sec === undefined) return '00:00';
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getPaceColor = (rating) => {
    switch (rating) {
      case 'OPTIMAL':
        return '#10b981'; // Emerald
      case 'RUSHED':
        return '#f59e0b'; // Amber
      case 'SLOW':
        return '#6366f1'; // Indigo
      default:
        return '#10b981';
    }
  };

  const getModalityColor = (modality) => {
    switch (modality) {
      case 'BOARD_WRITING':
        return '#10b981';
      case 'PPT_PRESENTATION':
        return '#f59e0b';
      case 'CLASSROOM_INTERACTION':
        return '#06b6d4';
      default:
        return '#6366f1';
    }
  };

  const meta = structuredData?.metadata;
  const topics = structuredData?.topic_segments || [];
  const syncTimeline = structuredData?.synchronized_timeline || [];
  const totalDuration = meta?.total_duration_sec || (topics.length > 0 ? topics[topics.length - 1].end_time_sec : 60.0);

  // Active sync point when inspecting hovered timestamp or first topic start
  const activeInspectTime = hoveredTime !== null ? hoveredTime : (selectedTopic ? selectedTopic.start_time_sec : 0.0);
  const activeSyncPoint = syncTimeline.find((p) => Math.abs(p.timestamp_sec - activeInspectTime) < (syncResolution * 1.2)) || syncTimeline[0];

  const handleDownloadContract = () => {
    if (!structuredData) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(structuredData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `structured_lecture_${sessionId}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header Controls Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-subtle)',
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              width: '2rem',
              height: '2rem',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#818cf8',
            }}
          >
            <Layers size={16} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Lecture Structuring & Multi-Track Handover
            </h4>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Module 4 • Multi-Track Synchronization, Chapter Segments & Structured Contract
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          {structuredData && (
            <>
              <button
                onClick={() => setShowJsonModal(true)}
                className="btn btn-secondary"
                style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', gap: '0.4rem' }}
                title="View JSON schema delivered to Member 2"
              >
                <Code size={14} />
                <span>Handover Contract</span>
              </button>

              <button
                onClick={handleDownloadContract}
                className="btn btn-secondary"
                style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', gap: '0.4rem' }}
              >
                <Download size={14} />
                <span>Export JSON</span>
              </button>
            </>
          )}

          <button
            onClick={handleRunStructuring}
            disabled={processing}
            className="btn btn-primary"
            style={{
              padding: '0.45rem 1rem',
              fontSize: '0.8rem',
              gap: '0.4rem',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            }}
          >
            {processing ? (
              <>
                <RefreshCw size={14} className="spin-icon" />
                <span>Structuring Lecture...</span>
              </>
            ) : (
              <>
                <Sparkles size={14} />
                <span>Run Structuring</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div style={{ padding: '3.5rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={28} className="spin-icon" style={{ margin: '0 auto 0.75rem', opacity: 0.7, color: 'var(--accent-primary)' }} />
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            Loading Multi-Modal Structured Lecture...
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Synchronizing Speech Transcripts, Video Intelligence & Slide Decks
          </p>
        </div>
      ) : !structuredData || topics.length === 0 ? (
        <div
          style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            border: '1px dashed var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <div
            style={{
              width: '3.5rem',
              height: '3.5rem',
              borderRadius: '50%',
              background: 'rgba(99, 102, 241, 0.12)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#818cf8',
            }}
          >
            <Layers size={28} />
          </div>
          <div>
            <h3 style={{ margin: '0 0 0.4rem', fontSize: '1.15rem', fontWeight: 700 }}>
              Ready to Structure Lecture & Synchronize Media
            </h3>
            <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-secondary)', maxWidth: '480px', lineHeight: 1.5 }}>
              Synthesizes Audio Intelligence (transcripts & diarization), OpenCV Video Intelligence (scenes & presence), and Slide Decks into a unified multi-track chaptered lecture asset for Member 2 handover.
            </p>
          </div>
          <button
            onClick={handleRunStructuring}
            disabled={processing}
            className="btn btn-primary"
            style={{
              padding: '0.65rem 1.5rem',
              fontSize: '0.88rem',
              gap: '0.5rem',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            }}
          >
            {processing ? (
              <>
                <RefreshCw size={16} className="spin-icon" />
                <span>Structuring Multi-Track Lecture...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Run Structuring Pipeline</span>
              </>
            )}
          </button>
        </div>
      ) : (
        <>
          {/* Pedagogical Pacing & Multi-Modal Analytics Cards */}
          {meta && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
              {/* Speaking Pace */}
              <div
                style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-lg)',
                  background: 'rgba(99, 102, 241, 0.06)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#818cf8' }}>Speaking Pace</span>
                  <Gauge size={16} color="#818cf8" />
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
                  <span style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    {meta.words_per_minute}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>WPM</span>
                </div>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    color: getPaceColor(meta.pace_rating),
                    background: `${getPaceColor(meta.pace_rating)}18`,
                    padding: '0.15rem 0.4rem',
                    borderRadius: '4px',
                    display: 'inline-block',
                    marginTop: '0.35rem',
                  }}
                >
                  ● {meta.pace_rating} PACE
                </span>
              </div>

              {/* Dialogue Ratio */}
              <div
                style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-lg)',
                  background: 'rgba(168, 85, 247, 0.06)',
                  border: '1px solid rgba(168, 85, 247, 0.2)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#c084fc' }}>Dialogue Balance</span>
                  <Users size={16} color="#c084fc" />
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {Math.round(meta.teacher_talk_ratio * 100)}% / {Math.round(meta.student_talk_ratio * 100)}%
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Teacher vs Student talk ratio</span>
              </div>

              {/* Chapters & Topics */}
              <div
                style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-lg)',
                  background: 'rgba(16, 185, 129, 0.06)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#34d399' }}>Topic Chapters</span>
                  <BookOpen size={16} color="#34d399" />
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {meta.total_topic_segments}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Structured semantic sections</span>
              </div>

              {/* Sync Quality */}
              <div
                style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-lg)',
                  background: 'rgba(6, 182, 212, 0.06)',
                  border: '1px solid rgba(6, 182, 212, 0.2)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#22d3ee' }}>Sync Quality</span>
                  <CheckCircle2 size={16} color="#22d3ee" />
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {Math.round(meta.sync_quality_score * 100)}%
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Multi-track temporal alignment</span>
              </div>
            </div>
          )}


      {/* Multi-Track Synchronized Timeline Track */}
      {topics.length > 0 && (
        <div
          style={{
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Multi-Track Synchronized Timeline (Audio + Video + Slides + Topics)
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Click any block to seek player
            </span>
          </div>

          {/* Track 1: Topics */}
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Track 1: Topic Chapters</div>
            <div
              style={{
                height: '24px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(255, 255, 255, 0.04)',
                overflow: 'hidden',
                display: 'flex',
                position: 'relative',
              }}
            >
              {topics.map((top, idx) => {
                const widthPct = Math.max(2, ((top.duration_sec || 10) / totalDuration) * 100);
                const isSelected = selectedTopic?.segment_id === top.segment_id;
                return (
                  <div
                    key={top.segment_id}
                    onClick={() => {
                      setSelectedTopic(top);
                      if (onSeekToTimestamp) onSeekToTimestamp(top.start_time_sec);
                    }}
                    onMouseEnter={() => setHoveredTime(top.start_time_sec)}
                    onMouseLeave={() => setHoveredTime(null)}
                    title={`${top.title} (${formatTimestamp(top.start_time_sec)} - ${formatTimestamp(top.end_time_sec)})`}
                    style={{
                      width: `${widthPct}%`,
                      height: '100%',
                      background: isSelected ? 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)' : 'rgba(99, 102, 241, 0.35)',
                      borderRight: '1px solid rgba(0, 0, 0, 0.4)',
                      cursor: 'pointer',
                      fontSize: '0.65rem',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      paddingLeft: '0.4rem',
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    Ch {idx + 1}: {top.title}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Track 2: Visual Modality */}
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Track 2: Visual Modality (Lecturing / Board / Slides)</div>
            <div
              style={{
                height: '16px',
                borderRadius: 'var(--radius-sm)',
                background: 'rgba(255, 255, 255, 0.04)',
                overflow: 'hidden',
                display: 'flex',
                position: 'relative',
              }}
            >
              {(structuredData?.visual_events || []).map((evt) => {
                const widthPct = Math.max(1, ((evt.duration_sec || 5) / totalDuration) * 100);
                return (
                  <div
                    key={evt.event_id}
                    onClick={() => {
                      if (onSeekToTimestamp) onSeekToTimestamp(evt.start_time_sec);
                    }}
                    title={`${evt.label}: ${formatTimestamp(evt.start_time_sec)}`}
                    style={{
                      width: `${widthPct}%`,
                      height: '100%',
                      background: getModalityColor(evt.scene_type),
                      borderRight: '1px solid rgba(0, 0, 0, 0.3)',
                      cursor: 'pointer',
                      opacity: 0.85,
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* Timeline Time Labels */}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            <span>00:00</span>
            <span>{formatTimestamp(totalDuration)}</span>
          </div>
        </div>
      )}

      {/* Sync Point Inspector Bar */}
      {activeSyncPoint && (
        <div
          style={{
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(99, 102, 241, 0.05)',
            border: '1px dashed rgba(99, 102, 241, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.75rem',
            fontSize: '0.78rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={14} color="#818cf8" />
            <strong style={{ color: '#818cf8' }}>Sync Checkpoint @ {formatTimestamp(activeSyncPoint.timestamp_sec)}:</strong>
            <span style={{ color: 'var(--text-secondary)' }}>
              {activeSyncPoint.speech_text ? `"${activeSyncPoint.speech_text.slice(0, 75)}..."` : 'Ambient silence / media transition'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.08)', fontSize: '0.7rem' }}>
              Speaker: {activeSyncPoint.speaker || 'Teacher'}
            </span>
            <span className="badge" style={{ background: `${getModalityColor(activeSyncPoint.visual_scene)}22`, color: getModalityColor(activeSyncPoint.visual_scene), fontSize: '0.7rem' }}>
              Scene: {activeSyncPoint.visual_scene}
            </span>
            {activeSyncPoint.slide_number && (
              <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', fontSize: '0.7rem' }}>
                Slide #{activeSyncPoint.slide_number}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Chapter Outline List & Details Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Selected Chapter Details */}
        {selectedTopic && (
          <div
            className="glass-card"
            style={{
              padding: '1.25rem',
              borderRadius: 'var(--radius-lg)',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Chapter Detail
                </span>
                <h4 style={{ margin: '0.2rem 0 0', fontSize: '1.1rem', fontWeight: 700 }}>
                  {selectedTopic.title}
                </h4>
              </div>
              <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.08)' }}>
                {formatTimestamp(selectedTopic.start_time_sec)} – {formatTimestamp(selectedTopic.end_time_sec)}
              </span>
            </div>

            <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {selectedTopic.summary}
            </p>

            {/* Key Concepts Chips */}
            {selectedTopic.key_concepts && selectedTopic.key_concepts.length > 0 && (
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                  Key Concepts & Terminology:
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {selectedTopic.key_concepts.map((concept, i) => (
                    <span
                      key={i}
                      style={{
                        fontSize: '0.72rem',
                        padding: '0.15rem 0.5rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.25)',
                        color: '#a5b4fc',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                      }}
                    >
                      <Tag size={10} />
                      {concept}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Primary Speaker</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {selectedTopic.primary_speaker}
                </span>
              </div>
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Dominant Modality</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: getModalityColor(selectedTopic.dominant_modality) }}>
                  {selectedTopic.dominant_modality}
                </span>
              </div>
            </div>

            {onSeekToTimestamp && (
              <button
                onClick={() => onSeekToTimestamp(selectedTopic.start_time_sec)}
                className="btn btn-secondary"
                style={{ width: '100%', gap: '0.5rem', justifyContent: 'center', fontSize: '0.82rem' }}
              >
                <Play size={14} />
                <span>Jump Player to {formatTimestamp(selectedTopic.start_time_sec)}</span>
              </button>
            )}
          </div>
        )}

        {/* Chapter Table of Contents Feed */}
        <div
          style={{
            maxHeight: '360px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.6rem',
            paddingRight: '0.35rem',
          }}
        >
          {topics.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
              <Layers size={32} style={{ opacity: 0.4, marginBottom: '0.5rem' }} />
              <p style={{ fontSize: '0.85rem', margin: 0 }}>No structured topics yet.</p>
              <span style={{ fontSize: '0.75rem' }}>Click "Run Structuring" to segment the lecture into chapters.</span>
            </div>
          ) : (
            topics.map((top, idx) => {
              const isSelected = selectedTopic?.segment_id === top.segment_id;

              return (
                <div
                  key={top.segment_id}
                  onClick={() => {
                    setSelectedTopic(top);
                    if (onSeekToTimestamp) onSeekToTimestamp(top.start_time_sec);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                    border: isSelected ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div
                      style={{
                        width: '1.85rem',
                        height: '1.85rem',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(99, 102, 241, 0.15)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        color: '#818cf8',
                      }}
                    >
                      {idx + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {top.title}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        Duration: {Math.round(top.duration_sec)}s • {top.primary_speaker}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {formatTimestamp(top.start_time_sec)}
                    </span>
                    <ChevronRight size={14} color="var(--text-muted)" />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
      </>
      )}

      {/* Handover Contract JSON Modal */}
      {showJsonModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.85)',
            zIndex: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
          }}
        >
          <div
            className="glass-card"
            style={{
              width: '800px',
              maxWidth: '92vw',
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-xl)',
              padding: '1.5rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Member 1 → Member 2 Handover Asset</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Clean interface delivered to Academic Reasoning, Curriculum Mapping & RAG
                </span>
              </div>
              <button className="btn btn-secondary" onClick={() => setShowJsonModal(false)} style={{ padding: '0.35rem 0.75rem' }}>
                Close
              </button>
            </div>

            <pre
              style={{
                flex: 1,
                overflow: 'auto',
                background: '#090d16',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.75rem',
                fontFamily: 'var(--font-mono)',
                color: '#38bdf8',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {JSON.stringify(structuredData, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
