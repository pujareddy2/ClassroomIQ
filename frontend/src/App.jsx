import React, { useState } from 'react';
import Navbar from './components/Navbar';
import LiveRecorder from './components/LiveRecorder';
import LectureUploader from './components/LectureUploader';
import SessionList from './components/SessionList';
import { api } from './services/api';
import { GraduationCap, LogIn, AlertCircle } from 'lucide-react';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('classroomiq_token'));
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'upload' | 'sessions'
  const [email, setEmail] = useState('faculty@classroomiq.ai');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await api.login({ email, password });
      setToken(localStorage.getItem('classroomiq_token'));
    } catch (err) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    api.logout();
    setToken(null);
  };

  const handleSessionCreated = (sessionData) => {
    setTimeout(() => {
      setActiveTab('sessions');
    }, 1500);
  };

  if (!token) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'radial-gradient(circle at top, var(--bg-secondary) 0%, var(--bg-primary) 100%)',
          padding: '1.5rem',
        }}
      >
        <div
          className="glass-card"
          style={{
            maxWidth: '420px',
            width: '100%',
            padding: '2.5rem 2rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.75rem',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
          }}
        >
          {/* Logo */}
          <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '3.5rem',
                height: '3.5rem',
                borderRadius: 'var(--radius-lg)',
                background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 24px rgba(99, 102, 241, 0.5)',
              }}
            >
              <GraduationCap size={32} color="#ffffff" />
            </div>
            <div>
              <h2
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.6rem',
                  fontWeight: 800,
                  letterSpacing: '-0.03em',
                  background: 'linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  marginBottom: '0.25rem',
                }}
              >
                ClassroomIQ
              </h2>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Faculty Intelligence & Analytics Portal
              </p>
            </div>
          </div>

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {error && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(244, 63, 94, 0.12)',
                  border: '1px solid rgba(244, 63, 94, 0.3)',
                  color: '#fb7185',
                  fontSize: '0.8rem',
                }}
              >
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="faculty@classroomiq.ai"
              />
            </div>

            <div>
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.85rem' }} disabled={loading}>
              <LogIn size={16} />
              {loading ? 'Authenticating...' : 'Sign In as Faculty'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} onLogout={handleLogout} />

      <main className="app-container" style={{ flex: 1 }}>
        {activeTab === 'live' && <LiveRecorder onSessionCreated={handleSessionCreated} />}
        {activeTab === 'upload' && <LectureUploader onUploadComplete={handleSessionCreated} />}
        {activeTab === 'sessions' && <SessionList />}
      </main>

      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '1.5rem 0',
          textAlign: 'center',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          marginTop: 'auto',
        }}
      >
        <div className="app-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <p style={{ margin: 0 }}>
            ClassroomIQ — AI Classroom Intelligence & Teaching Quality Platform
          </p>
          <button
            onClick={handleLogout}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent-rose)',
              cursor: 'pointer',
              fontSize: '0.78rem',
              fontWeight: 600,
            }}
          >
            Sign Out
          </button>
        </div>
      </footer>
    </div>
  );
}
