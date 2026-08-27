import React, { useState, useEffect } from 'react';
import {
  Mic,
  MessageSquare,
  Sparkles,
  Search,
  User,
  Users,
  Play,
  CheckCircle2,
  Clock,
  RefreshCw,
  Layers,
  ChevronRight,
  ChevronDown,
  BookOpen,
  Sliders,
  Globe,
  Radio,
  Cpu,
} from 'lucide-react';
import { api } from '../services/api';

export default function TranscriptViewer({ sessionId, onSeekToTimestamp }) {
  const [transcriptData, setTranscriptData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [speakerFilter, setSpeakerFilter] = useState('ALL');
  const [academicSyncSuccess, setAcademicSyncSuccess] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStatus, setJobStatus] = useState(null);

  // Adaptable Speech Engine Settings
  const [domainSubject, setDomainSubject] = useState('cs');
  const [diarizationMode, setDiarizationMode] = useState('lecture');
  const [language, setLanguage] = useState('auto');
  const [modelSize, setModelSize] = useState('base');

  const fetchTranscript = async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const res = await api.getTranscript(sessionId);
      setTranscriptData(res);
    } catch (err) {
      console.error('Failed to fetch transcript:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTranscript();
  }, [sessionId]);

  const handleProcessAudio = async () => {
    try {
      setProcessing(true);
      setAcademicSyncSuccess(false);
      setJobProgress(0);
      setJobStatus('PENDING');

      // Step 1: Submit the job — returns job_id immediately (< 1s)
      const jobRes = await api.processAudio(sessionId, {
        domain_subject: domainSubject,
        diarization_mode: diarizationMode,
        language: language,
        model_size: modelSize,
        boost_audio_volume: true,
        enable_vad: true,
        enable_diarization: true,
        sync_academic: true,
      });

      const jobId = jobRes?.job_id;
      if (!jobId) throw new Error('No job_id returned from server.');

      // Step 2: Poll for progress every 3 seconds
      const finalJob = await api.pollJobUntilDone(
        jobId,
        (progress, status) => {
          setJobProgress(progress);
          setJobStatus(status);
        },
        3000,
      );

      if (finalJob.status === 'FAILED') {
        throw new Error(finalJob.error_message || 'Audio processing failed on the server.');
      }

      // Step 3: Fetch the completed transcript
      const transcript = await api.getTranscript(sessionId);
      setTranscriptData({
        has_transcript: true,
        language: transcript.language,
        total_words: transcript.total_words,
        diarization_summary: transcript.diarization_summary,
        segments: transcript.segments,
      });
      if (transcript.academic_synced || finalJob.result_summary?.academic_synced) {
        setAcademicSyncSuccess(true);
      }
    } catch (err) {
      alert(`Audio processing failed: ${err.message}`);
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

  const segments = transcriptData?.segments || [];
  const summary = transcriptData?.diarization_summary;

  // Extract unique speaker names in the transcript
  const uniqueSpeakers = Array.from(new Set(segments.map((s) => s.speaker))).filter(Boolean);

  const filteredSegments = segments.filter((seg) => {
    const matchesSearch = seg.text.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSpeaker = speakerFilter === 'ALL' || seg.speaker === speakerFilter;
    return matchesSearch && matchesSpeaker;
  });

  const getSpeakerBadgeStyle = (speaker) => {
    if (speaker === 'Teacher') {
      return { bg: 'rgba(99, 102, 241, 0.2)', border: 'rgba(99, 102, 241, 0.4)', text: '#a5b4fc' };
    }
    if (speaker === 'Student') {
      return { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgba(16, 185, 129, 0.4)', text: '#6ee7b7' };
    }
    if (speaker === 'Speaker 1') {
      return { bg: 'rgba(59, 130, 246, 0.2)', border: 'rgba(59, 130, 246, 0.4)', text: '#93c5fd' };
    }
    if (speaker === 'Speaker 2') {
      return { bg: 'rgba(236, 72, 153, 0.2)', border: 'rgba(236, 72, 153, 0.4)', text: '#f472b6' };
    }
    if (speaker === 'Speaker 3') {
      return { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgba(245, 158, 11, 0.4)', text: '#fcd34d' };
    }
    return { bg: 'rgba(139, 92, 246, 0.2)', border: 'rgba(139, 92, 246, 0.4)', text: '#c4b5fd' };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Controls & Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MessageSquare size={18} color="var(--accent-primary)" />
          <h3 style={{ fontSize: '1.1rem' }}>Diarized Speech Transcript</h3>
          {transcriptData?.has_transcript && (
            <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.5rem', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontWeight: 600 }}>
              Whisper {modelSize.toUpperCase()}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {/* Settings Toggle Button */}
          <button
            className="btn btn-secondary"
            style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem' }}
            onClick={() => setShowSettings((prev) => !prev)}
            title="Configure Speech Recognition & Diarization parameters"
          >
            <Sliders size={14} />
            Options {showSettings ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>

          <button
            className="btn btn-primary"
            disabled={processing}
            onClick={handleProcessAudio}
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.82rem' }}
          >
            <Sparkles size={14} className={processing ? 'animate-spin' : ''} />
            {processing ? 'Transcribing Audio...' : transcriptData?.has_transcript ? 'Re-Transcribe' : 'Transcribe Audio'}
          </button>
        </div>
      </div>

      {/* Expandable Adaptability Configuration Panel */}
      {showSettings && (
        <div
          style={{
            background: 'var(--bg-tertiary)',
            padding: '1rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
            <Cpu size={14} />
            <span>AI Speech & Audio Adaptability Configuration</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.85rem', fontSize: '0.8rem' }}>
            {/* Subject Area */}
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontSize: '0.75rem' }}>
                Subject Domain Vocabulary
              </label>
              <select
                className="form-select"
                style={{ width: '100%', padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
                value={domainSubject}
                onChange={(e) => setDomainSubject(e.target.value)}
              >
                <option value="cs">Computer Science & Algorithms</option>
                <option value="engineering">Engineering & Circuits</option>
                <option value="math">Mathematics & Calculus</option>
                <option value="medical">Medical & Biology</option>
                <option value="business">Business & Economics</option>
                <option value="general">General Academics</option>
              </select>
            </div>

            {/* Conversation / Diarization Mode */}
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontSize: '0.75rem' }}>
                Conversation Type
              </label>
              <select
                className="form-select"
                style={{ width: '100%', padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
                value={diarizationMode}
                onChange={(e) => setDiarizationMode(e.target.value)}
              >
                <option value="lecture">Classroom Lecture (Teacher vs Student)</option>
                <option value="discussion">Group Discussion (Multi-Speaker)</option>
                <option value="solo">Solo Presentation / Monologue</option>
              </select>
            </div>

            {/* Language */}
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontSize: '0.75rem' }}>
                Language & Accent
              </label>
              <select
                className="form-select"
                style={{ width: '100%', padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="auto">Auto-Detect (Global / Hinglish / Accents)</option>
                <option value="en">English (Global)</option>
                <option value="hi">Hindi / Hinglish</option>
              </select>
            </div>

            {/* Whisper Model Quality */}
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontSize: '0.75rem' }}>
                Whisper AI Model
              </label>
              <select
                className="form-select"
                style={{ width: '100%', padding: '0.4rem 0.6rem', fontSize: '0.8rem' }}
                value={modelSize}
                onChange={(e) => setModelSize(e.target.value)}
              >
                <option value="base">Base (Balanced — Recommended)</option>
                <option value="small">Small (High Accuracy)</option>
                <option value="tiny">Tiny (Fastest)</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* When Transcript is Not Yet Generated */}
      {loading ? (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
          <p style={{ fontSize: '0.85rem' }}>Loading transcript...</p>
        </div>
      ) : processing ? (
        <div
          style={{
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          <RefreshCw size={28} className="animate-spin" color="var(--accent-primary)" style={{ margin: '0 auto' }} />
          <div>
            <p style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.25rem' }}>
              {jobStatus === 'RUNNING' ? 'Whisper AI is transcribing your lecture...' : 'Queuing transcription job...'}
            </p>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              This runs in the background. You can leave and come back — progress is saved.
            </p>
          </div>
          {jobProgress > 0 && (
            <div style={{ maxWidth: '340px', margin: '0 auto', width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                <span>{jobStatus}</span>
                <span>{jobProgress}%</span>
              </div>
              <div className="vu-meter-bar" style={{ height: '8px', borderRadius: '4px' }}>
                <div
                  className="vu-meter-fill"
                  style={{
                    width: `${jobProgress}%`,
                    background: 'linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)',
                    transition: 'width 0.8s ease',
                  }}
                />
              </div>
            </div>
          )}
        </div>
      ) : !transcriptData?.has_transcript || segments.length === 0 ? (
        <div
          style={{
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            background: 'var(--bg-tertiary)',
            borderRadius: 'var(--radius-md)',
            border: '1px dashed var(--border-subtle)',
          }}
        >
          <Mic size={36} color="var(--accent-primary)" style={{ margin: '0 auto 0.75rem', opacity: 0.8 }} />
          <h4 style={{ fontSize: '1rem', marginBottom: '0.35rem' }}>Ready to Transcribe Audio</h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', maxWidth: '420px', margin: '0 auto 1.25rem' }}>
            Transcribe raw audio/video into sentence-level timestamps, speaker attribution, and domain-adapted technical vocabulary.
          </p>
          <button className="btn btn-primary" onClick={handleProcessAudio} disabled={processing}>
            <Sparkles size={16} />
            {processing ? 'Processing Audio Pipeline...' : 'Start Whisper AI Transcription'}
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Diarization Metrics Bar */}
          {summary && (
            <div
              style={{
                background: 'var(--bg-tertiary)',
                padding: '0.85rem 1.25rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <User size={13} color="var(--accent-primary)" />
                  Primary Speaker: <strong style={{ color: 'var(--text-primary)' }}>{Math.round(summary.teacher_talk_ratio * 100)}%</strong> ({summary.teacher_speaking_time_sec}s)
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Users size={13} color="var(--accent-emerald)" />
                  Other Participants: <strong style={{ color: 'var(--text-primary)' }}>{Math.round((1 - summary.teacher_talk_ratio) * 100)}%</strong> ({summary.student_speaking_time_sec}s)
                </span>
              </div>

              {/* Ratio Bar */}
              <div className="vu-meter-bar" style={{ height: '6px' }}>
                <div
                  className="vu-meter-fill"
                  style={{
                    width: `${summary.teacher_talk_ratio * 100}%`,
                    background: 'linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)',
                  }}
                />
              </div>

              {academicSyncSuccess && (
                <div style={{ fontSize: '0.75rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.25rem' }}>
                  <CheckCircle2 size={13} />
                  <span>Synchronized with Member 2 Academic & Curriculum Intelligence Engine</span>
                </div>
              )}
            </div>
          )}

          {/* Search & Speaker Filter Bar */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                className="form-input"
                style={{ paddingLeft: '2.2rem', padding: '0.5rem 0.75rem 0.5rem 2.2rem', fontSize: '0.82rem' }}
                placeholder="Search transcript keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <select
              className="form-select"
              style={{ width: '150px', padding: '0.5rem', fontSize: '0.82rem' }}
              value={speakerFilter}
              onChange={(e) => setSpeakerFilter(e.target.value)}
            >
              <option value="ALL">All Speakers ({uniqueSpeakers.length})</option>
              {uniqueSpeakers.map((spk) => (
                <option key={spk} value={spk}>{spk}</option>
              ))}
            </select>
          </div>

          {/* Transcript Segments List */}
          <div
            style={{
              maxHeight: '400px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem',
              paddingRight: '0.35rem',
            }}
          >
            {filteredSegments.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem', padding: '2rem' }}>
                No segments match your search.
              </p>
            ) : (
              filteredSegments.map((seg, idx) => {
                const badgeStyle = getSpeakerBadgeStyle(seg.speaker);
                return (
                  <div
                    key={seg.segment_id || idx}
                    style={{
                      background: 'rgba(23, 30, 48, 0.6)',
                      border: `1px solid ${badgeStyle.border}`,
                      borderRadius: 'var(--radius-md)',
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem',
                      transition: 'all 0.15s ease',
                      cursor: onSeekToTimestamp ? 'pointer' : 'default',
                    }}
                    onClick={() => onSeekToTimestamp && onSeekToTimestamp(seg.start_time)}
                    title={onSeekToTimestamp ? 'Click to seek media player to this timestamp' : ''}
                  >
                    {/* Segment Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          background: badgeStyle.bg,
                          color: badgeStyle.text,
                        }}
                      >
                        {seg.speaker}
                      </span>

                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.75rem',
                          color: 'var(--accent-primary)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          background: 'rgba(10, 13, 20, 0.5)',
                          padding: '0.15rem 0.45rem',
                          borderRadius: '4px',
                        }}
                      >
                        <Clock size={11} />
                        {formatTimestamp(seg.start_time)} - {formatTimestamp(seg.end_time)}
                      </span>
                    </div>

                    {/* Spoken Text */}
                    <p style={{ fontSize: '0.86rem', color: 'var(--text-primary)', lineHeight: 1.45 }}>
                      {seg.text}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
