import React, { useState } from 'react';
import Navbar from './components/Navbar';
import LiveRecorder from './components/LiveRecorder';
import LectureUploader from './components/LectureUploader';
import SessionList from './components/SessionList';

export default function App() {
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'upload' | 'sessions'

  const handleSessionCreated = (sessionData) => {
    // Switch to sessions tab after recording / upload
    setTimeout(() => {
      setActiveTab('sessions');
    }, 1500);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

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
        <div className="app-container">
          <p>
            ClassroomIQ — AI Classroom Intelligence & Teaching Quality Platform • Module 1 (Classroom Capture & Multimedia)
          </p>
        </div>
      </footer>
    </div>
  );
}
