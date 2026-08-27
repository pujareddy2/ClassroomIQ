import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  X,
  Code2,
  Share2,
  Sparkles,
  Layers,
  Cpu,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';
import { api } from '../services/api';

export default function HandoverContractModal({ sessionId, onClose }) {
  const [contractData, setContractData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('tree'); // 'tree' | 'raw'

  useEffect(() => {
    if (!sessionId) return;
    fetchHandoverContract();
  }, [sessionId]);

  const fetchHandoverContract = async () => {
    try {
      setLoading(true);
      const res = await api.getHandoverContract(sessionId);
      setContractData(res);
    } catch (err) {
      console.error('Failed to fetch handover contract:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyJson = () => {
    if (!contractData) return;
    navigator.clipboard.writeText(JSON.stringify(contractData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPackage = () => {
    if (!sessionId) return;
    window.open(`http://127.0.0.1:8000/api/v1/multimedia/session/${sessionId}/export`, '_blank');
  };

  const metadata = contractData?.metadata || {};
  const transcriptCount = contractData?.transcript_segments?.length || 0;
  const visualCount = contractData?.visual_events?.length || 0;
  const topicCount = contractData?.topic_segments?.length || 0;
  const syncCount = contractData?.synchronized_timeline?.length || 0;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(5, 7, 15, 0.82)',
        backdropFilter: 'blur(10px)',
        zIndex: 1100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <div
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          width: '100%',
          maxWidth: '920px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          overflow: 'hidden',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'rgba(255, 255, 255, 0.02)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: 'var(--radius-md)',
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Share2 size={20} color="var(--accent-primary)" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>
                Member 1 Handover Contract
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
                Multi-Modal Perception Payload for Member 2 (Academic Intelligence)
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <button
              className="btn btn-secondary"
              onClick={handleCopyJson}
              disabled={loading || !contractData}
              style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
            >
              {copied ? <Check size={14} color="#34d399" /> : <Copy size={14} />}
              {copied ? 'Copied' : 'Copy JSON'}
            </button>

            <button
              className="btn btn-primary"
              onClick={handleDownloadPackage}
              disabled={loading || !contractData}
              style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem' }}
            >
              <Download size={14} />
              Export Package
            </button>

            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '0.35rem',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Contract Key Metrics Banner */}
        {!loading && contractData && (
          <div
            style={{
              padding: '0.85rem 1.5rem',
              background: 'rgba(99, 102, 241, 0.05)',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: '1rem',
            }}
          >
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Course / Title</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {contractData.course_name}
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Speech Segments</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#818cf8' }}>
                {transcriptCount} segments
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Visual Events</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fb7185' }}>
                {visualCount} scenes
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Topic Chapters</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#34d399' }}>
                {topicCount} topics
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Sync Quality</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#22d3ee' }}>
                {Math.round((metadata.sync_quality_score || 0.95) * 100)}%
              </div>
            </div>
          </div>
        )}

        {/* Toggle View Sub-header */}
        <div
          style={{
            padding: '0.5rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            gap: '0.5rem',
            background: 'var(--bg-tertiary)',
          }}
        >
          <button
            onClick={() => setActiveTab('tree')}
            style={{
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.78rem',
              fontWeight: 600,
              border: 'none',
              background: activeTab === 'tree' ? 'var(--accent-primary)' : 'transparent',
              color: activeTab === 'tree' ? '#ffffff' : 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Layers size={13} />
            Contract Data Schema
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            style={{
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.78rem',
              fontWeight: 600,
              border: 'none',
              background: activeTab === 'raw' ? 'var(--accent-primary)' : 'transparent',
              color: activeTab === 'raw' ? '#ffffff' : 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Code2 size={13} />
            Raw JSON Output
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.25rem 1.5rem', overflowY: 'auto', flex: 1 }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
              <Sparkles size={32} className="animate-spin" style={{ margin: '0 auto 1rem', color: 'var(--accent-primary)' }} />
              <p style={{ fontSize: '0.9rem' }}>Compiling Member 1 Handover Contract payload...</p>
            </div>
          ) : activeTab === 'tree' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Contract Sections */}
              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--border-subtle)',
                  padding: '1rem',
                }}
              >
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#818cf8', marginBottom: '0.6rem' }}>
                  1. Transcript Segments (`transcript_segments`)
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Sentence-level diarized text with exact start/end timestamps and speaker tags (Teacher / Student).
                </div>
                <div style={{ maxHeight: '180px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {(contractData?.transcript_segments || []).slice(0, 5).map((seg, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '0.4rem 0.6rem',
                        background: 'rgba(0,0,0,0.2)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.75rem',
                        display: 'flex',
                        gap: '0.6rem',
                      }}
                    >
                      <span style={{ color: 'var(--accent-primary)', fontWeight: 600, minWidth: '45px' }}>
                        [{Math.floor(seg.start_time || 0)}s]
                      </span>
                      <span style={{ color: '#a855f7', fontWeight: 600, minWidth: '65px' }}>
                        {seg.speaker}:
                      </span>
                      <span style={{ color: 'var(--text-primary)', flex: 1 }}>{seg.text}</span>
                    </div>
                  ))}
                  {transcriptCount > 5 && (
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center', paddingTop: '0.2rem' }}>
                      ... and {transcriptCount - 5} more speech segments
                    </div>
                  )}
                </div>
              </div>

              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--border-subtle)',
                  padding: '1rem',
                }}
              >
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#34d399', marginBottom: '0.6rem' }}>
                  2. Synchronized Topic Chapters (`topic_segments`)
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                  Multi-modal semantic sections aligning speech topics with presentation slides and board work.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {(contractData?.topic_segments || []).map((top, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '0.5rem 0.75rem',
                        background: 'rgba(16, 185, 129, 0.05)',
                        border: '1px solid rgba(16, 185, 129, 0.15)',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.78rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <strong style={{ color: '#34d399' }}>Chapter {i + 1}: {top.title}</strong>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          Keywords: {(top.keywords || []).join(', ')}
                        </div>
                      </div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {top.start_time_sec}s - {top.end_time_sec}s
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <pre
              style={{
                background: '#090d16',
                padding: '1rem',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
                color: '#38bdf8',
                fontSize: '0.78rem',
                fontFamily: 'monospace',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                margin: 0,
              }}
            >
              {JSON.stringify(contractData, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
