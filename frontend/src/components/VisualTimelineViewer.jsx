import React, { useState, useEffect } from 'react';
import {
  Eye,
  Video,
  Monitor,
  Edit3,
  Users,
  Play,
  Clock,
  Sparkles,
  RefreshCw,
  Layers,
  ChevronRight,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Activity,
  Maximize2,
  PieChart,
} from 'lucide-react';
import { api } from '../services/api';

export default function VisualTimelineViewer({ sessionId, onSeekToTimestamp }) {
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStatus, setJobStatus] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  // Settings
  const [sampleInterval, setSampleInterval] = useState(5.0);
  const [detectTeacher, setDetectTeacher] = useState(true);
  const [detectBoard, setDetectBoard] = useState(true);
  const [detectPpt, setDetectPpt] = useState(true);

  const fetchTimeline = async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const summaryRes = await api.getVideoSummary(sessionId);
      const timelineRes = await api.getVideoTimeline(sessionId);
      setTimelineData({
        summary: summaryRes,
        timeline: timelineRes,
      });
      if (timelineRes && timelineRes.length > 0) {
        setSelectedEvent(timelineRes[0]);
      }
    } catch (err) {
      console.error('Failed to load video timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [sessionId]);

  const handleProcessVideo = async () => {
    try {
      setProcessing(true);
      setJobProgress(0);
      setJobStatus('PENDING');

      const jobRes = await api.processVideo(sessionId, {
        sample_interval_sec: parseFloat(sampleInterval),
        detect_teacher: detectTeacher,
        detect_board: detectBoard,
        detect_ppt: detectPpt,
      });

      const jobId = jobRes?.job_id;
      if (!jobId) throw new Error('No job_id returned from server.');

      const finalJob = await api.pollJobUntilDone(
        jobId,
        (progress, status) => {
          setJobProgress(progress);
          setJobStatus(status);
        },
        2000,
      );

      if (finalJob.status === 'FAILED') {
        throw new Error(finalJob.error_message || 'Video processing failed on the server.');
      }

      await fetchTimeline();
    } catch (err) {
      alert(`Video intelligence processing failed: ${err.message}`);
    } finally {
      setProcessing(false);
      setJobProgress(0);
      setJobStatus(null);
    }
  };

  const formatTimestamp = (sec) => {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getSceneColor = (sceneType) => {
    switch (sceneType) {
      case 'TEACHER_LECTURING':
        return '#6366f1'; // Indigo
      case 'BOARD_WRITING':
        return '#10b981'; // Emerald
      case 'PPT_PRESENTATION':
        return '#f59e0b'; // Amber
      case 'CLASSROOM_INTERACTION':
        return '#06b6d4'; // Cyan
      default:
        return '#8b5cf6'; // Violet
    }
  };

  const getSceneIcon = (sceneType) => {
    switch (sceneType) {
      case 'TEACHER_LECTURING':
        return Eye;
      case 'BOARD_WRITING':
        return Edit3;
      case 'PPT_PRESENTATION':
        return Monitor;
      case 'CLASSROOM_INTERACTION':
        return Users;
      default:
        return Layers;
    }
  };

  const summary = timelineData?.summary;
  const events = timelineData?.timeline || [];
  const totalDuration = summary?.total_duration_sec || (events.length > 0 ? events[events.length - 1].end_time_sec : 60.0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Controls Bar */}
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
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(16, 185, 129, 0.2) 100%)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#818cf8',
            }}
          >
            <Video size={16} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              OpenCV Video Intelligence & Scene Timeline
            </h4>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Module 3 • Teacher Tracking, Board Detection & Slide Screen Analytics
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="btn btn-secondary"
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', gap: '0.4rem' }}
          >
            <Sliders size={14} />
            <span>CV Parameters</span>
          </button>

          <button
            onClick={handleProcessVideo}
            disabled={processing}
            className="btn btn-primary"
            style={{
              padding: '0.45rem 1rem',
              fontSize: '0.8rem',
              gap: '0.4rem',
              background: 'linear-gradient(135deg, #6366f1 0%, #10b981 100%)',
            }}
          >
            {processing ? (
              <>
                <RefreshCw size={14} className="spin-icon" />
                <span>Running Computer Vision...</span>
              </>
            ) : (
              <>
                <Sparkles size={14} />
                <span>Run Video Intelligence</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Advanced CV Settings Drawer */}
      {showSettings && (
        <div
          className="glass-card"
          style={{
            padding: '1rem 1.25rem',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-subtle)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
          }}
        >
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
              Sampling Interval
            </label>
            <select
              value={sampleInterval}
              onChange={(e) => setSampleInterval(e.target.value)}
              className="input-field"
              style={{ fontSize: '0.8rem', padding: '0.4rem' }}
            >
              <option value="2.0">Every 2 seconds (High Precision)</option>
              <option value="5.0">Every 5 seconds (Balanced)</option>
              <option value="10.0">Every 10 seconds (Fast)</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', justifyContent: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
              <input type="checkbox" checked={detectTeacher} onChange={(e) => setDetectTeacher(e.target.checked)} />
              <span>Teacher Detection & Tracking</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
              <input type="checkbox" checked={detectBoard} onChange={(e) => setDetectBoard(e.target.checked)} />
              <span>Board & Stroke Density</span>
            </label>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', justifyContent: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
              <input type="checkbox" checked={detectPpt} onChange={(e) => setDetectPpt(e.target.checked)} />
              <span>Digital PPT Slide Detection</span>
            </label>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div style={{ padding: '3.5rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={28} className="spin-icon" style={{ margin: '0 auto 0.75rem', opacity: 0.7, color: 'var(--accent-primary)' }} />
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            Loading OpenCV Video Intelligence...
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Retrieving Teacher Tracking, Board Detections & Presentation Events
          </p>
        </div>
      ) : !summary || summary.analyzed_frames_count === 0 || events.length === 0 ? (
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
            <Video size={28} />
          </div>
          <div>
            <h3 style={{ margin: '0 0 0.4rem', fontSize: '1.15rem', fontWeight: 700 }}>
              Ready to Run Video Intelligence Pipeline
            </h3>
            <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-secondary)', maxWidth: '480px', lineHeight: 1.5 }}>
              Executes OpenCV temporal frame extraction, teacher presence tracking, whiteboard/blackboard stroke density analysis, and digital PPT slide detection.
            </p>
          </div>
          <button
            onClick={handleProcessVideo}
            disabled={processing}
            className="btn btn-primary"
            style={{
              padding: '0.65rem 1.5rem',
              fontSize: '0.88rem',
              gap: '0.5rem',
              background: 'linear-gradient(135deg, #6366f1 0%, #10b981 100%)',
            }}
          >
            {processing ? (
              <>
                <RefreshCw size={16} className="spin-icon" />
                <span>Running Computer Vision Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Start Video Intelligence</span>
              </>
            )}
          </button>
        </div>
      ) : (
        <>
          {/* Metric Analytics Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            {/* Teacher Presence */}
            <div
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                background: 'rgba(99, 102, 241, 0.06)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#818cf8' }}>Teacher Presence</span>
                <Eye size={16} color="#818cf8" />
              </div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {Math.round((summary.teacher_presence_ratio || 0) * 100)}%
              </div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Instructor on camera stage</span>
            </div>

          {/* Board Writing */}
          <div
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-lg)',
              background: 'rgba(16, 185, 129, 0.06)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#34d399' }}>Board Writing</span>
              <Edit3 size={16} color="#34d399" />
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              {Math.round((summary.board_writing_ratio || 0) * 100)}%
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Chalk/Whiteboard activity</span>
          </div>

          {/* PPT Presentation */}
          <div
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-lg)',
              background: 'rgba(245, 158, 11, 0.06)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#fbbf24' }}>Slide Presentation</span>
              <Monitor size={16} color="#fbbf24" />
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              {Math.round((summary.ppt_presentation_ratio || 0) * 100)}%
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Digital screen projection</span>
          </div>

          {/* Scene Changes & Confidence */}
          <div
            style={{
              padding: '1rem',
              borderRadius: 'var(--radius-lg)',
              background: 'rgba(6, 182, 212, 0.06)',
              border: '1px solid rgba(6, 182, 212, 0.2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#22d3ee' }}>Scene Dynamics</span>
              <Activity size={16} color="#22d3ee" />
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              {summary.total_scene_changes || 0}{' '}
              <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-muted)' }}>transitions</span>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {summary.analyzed_frames_count} frames analyzed
            </span>
          </div>
        </div>

      {/* Visual Timeline Bar */}
      {events.length > 0 && (
        <div
          style={{
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            padding: '1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Interactive Visual Timeline
            </span>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#6366f1' }} />
                Lecturing
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
                Board Writing
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b' }} />
                Slide Deck
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#06b6d4' }} />
                Discussion
              </span>
            </div>
          </div>

          {/* Bar track */}
          <div
            style={{
              height: '32px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(255, 255, 255, 0.05)',
              overflow: 'hidden',
              display: 'flex',
              position: 'relative',
              boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.4)',
            }}
          >
            {events.map((evt) => {
              const widthPct = Math.max(1.5, ((evt.duration_sec || 5) / totalDuration) * 100);
              const color = getSceneColor(evt.scene_type);
              const isSelected = selectedEvent?.event_id === evt.event_id;

              return (
                <div
                  key={evt.event_id}
                  onClick={() => {
                    setSelectedEvent(evt);
                    if (onSeekToTimestamp) {
                      onSeekToTimestamp(evt.start_time_sec);
                    }
                  }}
                  title={`${evt.label}: ${formatTimestamp(evt.start_time_sec)} - ${formatTimestamp(evt.end_time_sec)}`}
                  style={{
                    width: `${widthPct}%`,
                    height: '100%',
                    background: color,
                    opacity: isSelected ? 1 : 0.85,
                    borderRight: '1px solid rgba(0, 0, 0, 0.3)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    position: 'relative',
                  }}
                />
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <span>00:00</span>
            <span>{formatTimestamp(totalDuration)}</span>
          </div>
        </div>
      )}

      {/* Selected Event Details & Event Feed */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Left: Selected Scene Inspector */}
        {selectedEvent && (
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: getSceneColor(selectedEvent.scene_type),
                  }}
                />
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>{selectedEvent.label}</h4>
              </div>
              <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.08)' }}>
                {formatTimestamp(selectedEvent.start_time_sec)} – {formatTimestamp(selectedEvent.end_time_sec)}
              </span>
            </div>

            <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {selectedEvent.description}
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Teacher Detected</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: selectedEvent.teacher_present ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                  {selectedEvent.teacher_present ? 'Active on Stage' : 'Not in Frame'}
                </span>
              </div>
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Board / Slide Activity</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: selectedEvent.board_active ? '#34d399' : selectedEvent.ppt_active ? '#fbbf24' : 'var(--text-muted)' }}>
                  {selectedEvent.board_active ? 'Active Board Work' : selectedEvent.ppt_active ? 'Slide Projection' : 'General View'}
                </span>
              </div>
            </div>

            {onSeekToTimestamp && (
              <button
                onClick={() => onSeekToTimestamp(selectedEvent.start_time_sec)}
                className="btn btn-secondary"
                style={{ width: '100%', gap: '0.5rem', justifyContent: 'center', fontSize: '0.82rem' }}
              >
                <Play size={14} />
                <span>Jump Video to {formatTimestamp(selectedEvent.start_time_sec)}</span>
              </button>
            )}
          </div>
        )}

        {/* Right: Visual Event Stream */}
        <div
          style={{
            maxHeight: '340px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.6rem',
            paddingRight: '0.35rem',
          }}
        >
          {events.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
              <Video size={32} style={{ opacity: 0.4, marginBottom: '0.5rem' }} />
              <p style={{ fontSize: '0.85rem', margin: 0 }}>No video analysis data yet.</p>
              <span style={{ fontSize: '0.75rem' }}>Click "Run Video Intelligence" above to analyze the lecture.</span>
            </div>
          ) : (
            events.map((evt) => {
              const isSelected = selectedEvent?.event_id === evt.event_id;
              const Icon = getSceneIcon(evt.scene_type);
              const color = getSceneColor(evt.scene_type);

              return (
                <div
                  key={evt.event_id}
                  onClick={() => {
                    setSelectedEvent(evt);
                    if (onSeekToTimestamp) {
                      onSeekToTimestamp(evt.start_time_sec);
                    }
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
                        width: '2rem',
                        height: '2rem',
                        borderRadius: 'var(--radius-md)',
                        background: `${color}22`,
                        border: `1px solid ${color}55`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: color,
                      }}
                    >
                      <Icon size={14} />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {evt.label}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        Duration: {Math.round(evt.duration_sec)}s
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {formatTimestamp(evt.start_time_sec)}
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
    </div>
  );
}

