import React, { useState, useEffect } from 'react';
import { Radio, UploadCloud, Film, Activity, GraduationCap, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function Navbar({ activeTab, onTabChange }) {
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.checkHealth();
        if (res.status === 'healthy' || res.status === 'ok') {
          setBackendStatus('online');
        } else {
          setBackendStatus('offline');
        }
      } catch {
        setBackendStatus('offline');
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'live', label: 'Live Studio', icon: Radio },
    { id: 'upload', label: 'Upload Lecture', icon: UploadCloud },
    { id: 'sessions', label: 'Sessions & Player', icon: Film },
  ];

  return (
    <header style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(10, 13, 20, 0.8)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 50, marginBottom: '2rem' }}>
      <div className="app-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '4.25rem', paddingBottom: 0 }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{ width: '2.5rem', height: '2.5rem', borderRadius: 'var(--radius-md)', background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)' }}>
            <GraduationCap size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: '1.25rem', letterSpacing: '-0.03em', background: 'linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                ClassroomIQ
              </span>
              <span style={{ fontSize: '0.65rem', padding: '0.15rem 0.45rem', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontWeight: 700, border: '1px solid rgba(99, 102, 241, 0.3)' }}>
                MODULE 1
              </span>
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Classroom Capture & Multimedia Intelligence</span>
          </div>
        </div>

        {/* Nav Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-secondary)', padding: '0.35rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  background: isActive ? 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--text-secondary)',
                  boxShadow: isActive ? '0 2px 10px rgba(99, 102, 241, 0.3)' : 'none',
                }}
              >
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Backend Health Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {backendStatus === 'online' ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-emerald)', background: 'rgba(16, 185, 129, 0.1)', padding: '0.35rem 0.75rem', borderRadius: '9999px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
              <CheckCircle2 size={14} />
              <span>FastAPI Online</span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-rose)', background: 'rgba(244, 63, 94, 0.1)', padding: '0.35rem 0.75rem', borderRadius: '9999px', border: '1px solid rgba(244, 63, 94, 0.25)' }}>
              <AlertCircle size={14} />
              <span>FastAPI Disconnected</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
