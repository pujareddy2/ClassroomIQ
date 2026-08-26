import React, { useState, useRef, useEffect } from 'react';
import {
  Camera,
  Mic,
  MicOff,
  Monitor,
  Play,
  Pause,
  Square,
  ShieldCheck,
  Radio,
  Clock,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertCircle,
  Video,
  VideoOff,
} from 'lucide-react';
import { api } from '../services/api';

export default function LiveRecorder({ onSessionCreated }) {
  // Session Configuration
  const [courseName, setCourseName] = useState('CS101 - Introduction to Computer Science');
  const [facultyName, setFacultyName] = useState('Dr. Alan Turing');
  const [lectureTitle, setLectureTitle] = useState('Lecture 01 — Algorithms & Control Flow');
  const [classroom, setClassroom] = useState('Auditorium 3B');
  const [consentConfirmed, setConsentConfirmed] = useState(true);
  const [screenShareActive, setScreenShareActive] = useState(false);

  // Hardware Devices
  const [videoDevices, setVideoDevices] = useState([]);
  const [audioDevices, setAudioDevices] = useState([]);
  const [selectedVideoDevice, setSelectedVideoDevice] = useState('');
  const [selectedAudioDevice, setSelectedAudioDevice] = useState('');

  // Hardware Toggles
  const [cameraEnabled, setCameraEnabled] = useState(true);
  const [micEnabled, setMicEnabled] = useState(true);

  // Recording State: 'IDLE' | 'RECORDING' | 'PAUSED' | 'FINALIZING' | 'COMPLETED'
  const [recordingState, setRecordingState] = useState('IDLE');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [chunkCount, setChunkCount] = useState(0);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [notification, setNotification] = useState(null);

  // Media Streams & Audio Analysis
  const webcamVideoRef = useRef(null);
  const screenVideoRef = useRef(null);
  const webcamStreamRef = useRef(null);
  const screenStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const chunkIndexRef = useRef(0);
  const timerIntervalRef = useRef(null);

  // Enumerate devices on mount
  useEffect(() => {
    async function getDevices() {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const vDevs = devices.filter((d) => d.kind === 'videoinput');
        const aDevs = devices.filter((d) => d.kind === 'audioinput');
        setVideoDevices(vDevs);
        setAudioDevices(aDevs);
        if (vDevs.length > 0) setSelectedVideoDevice(vDevs[0].deviceId);
        if (aDevs.length > 0) setSelectedAudioDevice(aDevs[0].deviceId);
      } catch (err) {
        console.warn('Device enumeration error:', err);
      }
    }
    getDevices();
  }, []);

  // Initialize Webcam Preview Stream & Audio VU Meter
  useEffect(() => {
    let active = true;

    async function setupWebcam() {
      if (!cameraEnabled && !micEnabled) return;
      try {
        if (webcamStreamRef.current) {
          webcamStreamRef.current.getTracks().forEach((t) => t.stop());
        }

        const constraints = {
          video: cameraEnabled ? (selectedVideoDevice ? { deviceId: { exact: selectedVideoDevice } } : true) : false,
          audio: micEnabled ? (selectedAudioDevice ? { deviceId: { exact: selectedAudioDevice } } : true) : false,
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        if (!active) return;

        webcamStreamRef.current = stream;
        if (webcamVideoRef.current) {
          webcamVideoRef.current.srcObject = stream;
        }

        // Setup Web Audio VU Meter
        if (micEnabled && stream.getAudioTracks().length > 0) {
          const AudioContext = window.AudioContext || window.webkitAudioContext;
          const ctx = new AudioContext();
          const source = ctx.createMediaStreamSource(stream);
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 256;
          source.connect(analyser);

          audioContextRef.current = ctx;
          analyserRef.current = analyser;

          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          const updateVU = () => {
            if (!analyserRef.current) return;
            analyserRef.current.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i];
            }
            const avg = sum / dataArray.length;
            setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)));
            animationFrameRef.current = requestAnimationFrame(updateVU);
          };
          updateVU();
        }
      } catch (err) {
        console.warn('Webcam stream setup error:', err);
      }
    }

    setupWebcam();

    return () => {
      active = false;
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, [selectedVideoDevice, selectedAudioDevice, cameraEnabled, micEnabled]);

  // Screen Share / Smart Board Stream
  const toggleScreenShare = async () => {
    if (screenShareActive) {
      if (screenStreamRef.current) {
        screenStreamRef.current.getTracks().forEach((t) => t.stop());
        screenStreamRef.current = null;
      }
      setScreenShareActive(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        screenStreamRef.current = stream;
        if (screenVideoRef.current) {
          screenVideoRef.current.srcObject = stream;
        }
        setScreenShareActive(true);

        stream.getVideoTracks()[0].onended = () => {
          setScreenShareActive(false);
        };
      } catch (err) {
        console.warn('Screen share cancelled:', err);
      }
    }
  };

  // Timer Formatter
  const formatTime = (totalSeconds) => {
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Start Live Recording Session
  const handleStartRecording = async () => {
    if (!consentConfirmed) {
      alert('Please confirm the classroom recording consent before starting.');
      return;
    }

    try {
      setRecordingState('RECORDING');
      setElapsedSeconds(0);
      setChunkCount(0);
      chunkIndexRef.current = 0;

      // 1. Initialize session on FastAPI backend
      const sessionInit = await api.startLiveSession({
        course_name_or_code: courseName,
        faculty_name: facultyName,
        title: lectureTitle,
        classroom,
        consent_confirmed: true,
        has_screen_share: screenShareActive,
      });

      const sessionId = sessionInit.session_id;
      setCurrentSessionId(sessionId);

      // 2. Select stream to record (composite / screen or webcam)
      const streamToRecord = screenShareActive && screenStreamRef.current ? screenStreamRef.current : webcamStreamRef.current;

      if (!streamToRecord) {
        throw new Error('No active camera or screen stream to record');
      }

      // Add audio track if screen share doesn't have mic
      const combinedTracks = [...streamToRecord.getVideoTracks()];
      if (webcamStreamRef.current && webcamStreamRef.current.getAudioTracks().length > 0) {
        combinedTracks.push(webcamStreamRef.current.getAudioTracks()[0]);
      }
      const combinedStream = new MediaStream(combinedTracks);

      // 3. Initialize MediaRecorder with 5s time slice
      const options = MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')
        ? { mimeType: 'video/webm;codecs=vp9,opus' }
        : MediaRecorder.isTypeSupported('video/webm')
        ? { mimeType: 'video/webm' }
        : {};

      const recorder = new MediaRecorder(combinedStream, options);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = async (e) => {
        if (e.data && e.data.size > 0) {
          const idx = chunkIndexRef.current++;
          setChunkCount((prev) => prev + 1);
          try {
            await api.uploadLiveChunk(sessionId, idx, e.data);
          } catch (chunkErr) {
            console.error('Failed to upload live chunk:', chunkErr);
          }
        }
      };

      recorder.start(5000); // 5-second chunk interval

      // Start elapsed timer
      timerIntervalRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);

      setNotification({ type: 'success', message: `Recording session active (${sessionId.slice(0, 8)}...)` });
    } catch (err) {
      setRecordingState('IDLE');
      setNotification({ type: 'error', message: `Failed to start session: ${err.message}` });
    }
  };

  // Pause / Resume
  const handlePauseResume = () => {
    if (!mediaRecorderRef.current) return;
    if (recordingState === 'RECORDING') {
      mediaRecorderRef.current.pause();
      setRecordingState('PAUSED');
      clearInterval(timerIntervalRef.current);
    } else if (recordingState === 'PAUSED') {
      mediaRecorderRef.current.resume();
      setRecordingState('RECORDING');
      timerIntervalRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    }
  };

  // Stop & Finalize
  const handleStopRecording = async () => {
    if (!mediaRecorderRef.current) return;

    setRecordingState('FINALIZING');
    clearInterval(timerIntervalRef.current);

    // Stop MediaRecorder (flushes remaining data)
    mediaRecorderRef.current.stop();

    try {
      // Allow slight buffer for last chunk
      setTimeout(async () => {
        const result = await api.completeLiveSession(currentSessionId, {
          duration_seconds: elapsedSeconds,
          course_name_or_code: courseName,
          faculty_name: facultyName,
          title: lectureTitle,
          classroom,
          notes: 'Captured via Live Classroom Studio',
        });

        setRecordingState('COMPLETED');
        setNotification({
          type: 'success',
          message: 'Lecture saved! FFmpeg extracted 16kHz audio & keyframes ready for AI intelligence.',
        });

        if (onSessionCreated) onSessionCreated(result);
      }, 1200);
    } catch (err) {
      setRecordingState('IDLE');
      setNotification({ type: 'error', message: `Finalize failed: ${err.message}` });
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '2rem', alignItems: 'start' }}>
      {/* ── Left Column: Live Video Canvas & Feed Previews ───────────────────── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Main Preview Container */}
        <div
          className="glass-card"
          style={{
            position: 'relative',
            background: '#070a12',
            borderRadius: 'var(--radius-xl)',
            overflow: 'hidden',
            padding: 0,
            border: recordingState === 'RECORDING' ? '2px solid rgba(244, 63, 94, 0.6)' : '1px solid var(--border-subtle)',
            boxShadow: recordingState === 'RECORDING' ? '0 0 32px rgba(244, 63, 94, 0.25)' : 'var(--shadow-card)',
          }}
        >
          {/* Main Feed Viewport */}
          <div style={{ position: 'relative', width: '100%', height: '480px', background: '#000000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {screenShareActive ? (
              <video ref={screenVideoRef} autoPlay playsInline muted style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            ) : cameraEnabled ? (
              <video ref={webcamVideoRef} autoPlay playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }} />
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <VideoOff size={48} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
                <p>Camera feed disabled</p>
              </div>
            )}

            {/* PiP Overlay if Screen Share AND Camera are both active */}
            {screenShareActive && cameraEnabled && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '1.25rem',
                  right: '1.25rem',
                  width: '180px',
                  height: '110px',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                  border: '2px solid rgba(99, 102, 241, 0.6)',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.8)',
                  background: '#000000',
                }}
              >
                <video ref={webcamVideoRef} autoPlay playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }} />
                <span style={{ position: 'absolute', bottom: '4px', left: '6px', fontSize: '0.65rem', background: 'rgba(0,0,0,0.7)', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                  Teacher
                </span>
              </div>
            )}

            {/* Live Indicator Badges */}
            <div style={{ position: 'absolute', top: '1.25rem', left: '1.25rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              {recordingState === 'RECORDING' && (
                <div className="badge badge-recording">
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f43f5e', display: 'inline-block' }} />
                  <span>REC LIVE</span>
                </div>
              )}
              {recordingState === 'PAUSED' && (
                <div className="badge badge-info" style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
                  <span>PAUSED</span>
                </div>
              )}
              {screenShareActive && (
                <div className="badge badge-info">
                  <Monitor size={12} />
                  <span>SMART BOARD / SCREEN</span>
                </div>
              )}
            </div>

            {/* Elapsed Timer Overlay */}
            {recordingState !== 'IDLE' && (
              <div
                style={{
                  position: 'absolute',
                  top: '1.25rem',
                  right: '1.25rem',
                  background: 'rgba(10, 13, 20, 0.85)',
                  padding: '0.4rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  backdropFilter: 'blur(8px)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <Clock size={15} color={recordingState === 'RECORDING' ? '#f43f5e' : '#f59e0b'} />
                <span>{formatTime(elapsedSeconds)}</span>
              </div>
            )}
          </div>

          {/* Bottom Bar: Audio VU Meter & Quick Stream Toggles */}
          <div style={{ padding: '1.25rem 1.75rem', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '2rem' }}>
            {/* Audio VU Meter */}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <Mic size={13} color={audioLevel > 5 ? 'var(--accent-emerald)' : 'var(--text-muted)'} />
                  Microphone Volume (VU)
                </span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>{audioLevel}%</span>
              </div>
              <div className="vu-meter-bar">
                <div className="vu-meter-fill" style={{ width: `${audioLevel}%` }} />
              </div>
            </div>

            {/* Stream Action Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                className={`btn ${cameraEnabled ? 'btn-secondary' : 'btn-danger'}`}
                style={{ padding: '0.5rem 0.85rem', fontSize: '0.82rem' }}
                onClick={() => setCameraEnabled(!cameraEnabled)}
              >
                {cameraEnabled ? <Camera size={16} /> : <VideoOff size={16} />}
                {cameraEnabled ? 'Cam ON' : 'Cam OFF'}
              </button>

              <button
                className={`btn ${micEnabled ? 'btn-secondary' : 'btn-danger'}`}
                style={{ padding: '0.5rem 0.85rem', fontSize: '0.82rem' }}
                onClick={() => setMicEnabled(!micEnabled)}
              >
                {micEnabled ? <Mic size={16} /> : <MicOff size={16} />}
                {micEnabled ? 'Mic ON' : 'Muted'}
              </button>

              <button
                className={`btn ${screenShareActive ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '0.5rem 0.85rem', fontSize: '0.82rem' }}
                onClick={toggleScreenShare}
              >
                <Monitor size={16} />
                {screenShareActive ? 'Stop Board Share' : 'Share Smart Board / Screen'}
              </button>
            </div>
          </div>
        </div>

        {/* Status Notification Banner */}
        {notification && (
          <div
            style={{
              padding: '1rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              background: notification.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
              border: `1px solid ${notification.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              color: notification.type === 'success' ? '#34d399' : '#fb7185',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              fontSize: '0.88rem',
            }}
          >
            {notification.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <span>{notification.message}</span>
          </div>
        )}
      </div>

      {/* ── Right Column: Session Controls & Metadata Form ─────────────────── */}
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
          <Radio size={20} color="var(--accent-primary)" />
          <h2 style={{ fontSize: '1.2rem' }}>Recording Controls</h2>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {recordingState === 'IDLE' || recordingState === 'COMPLETED' ? (
            <button className="btn btn-primary" style={{ padding: '0.9rem', fontSize: '1rem' }} onClick={handleStartRecording}>
              <Play size={18} fill="#ffffff" />
              Start Live Lecture Capture
            </button>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <button className="btn btn-secondary" onClick={handlePauseResume}>
                {recordingState === 'RECORDING' ? (
                  <>
                    <Pause size={16} /> Pause
                  </>
                ) : (
                  <>
                    <Play size={16} /> Resume
                  </>
                )}
              </button>

              <button className="btn btn-danger" onClick={handleStopRecording} disabled={recordingState === 'FINALIZING'}>
                <Square size={16} fill="#ffffff" />
                {recordingState === 'FINALIZING' ? 'Finalizing...' : 'Stop & Save'}
              </button>
            </div>
          )}

          {recordingState === 'RECORDING' && (
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.35rem' }}>
              <Layers size={13} />
              <span>Streaming 5s slices to FastAPI ({chunkCount} chunks received)</span>
            </div>
          )}
        </div>

        {/* Consent & Opt-In (EPB §7.7.1) */}
        <div style={{ background: 'rgba(99, 102, 241, 0.06)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '0.85rem', borderRadius: 'var(--radius-md)', display: 'flex', gap: '0.65rem' }}>
          <input
            type="checkbox"
            id="consent-check"
            checked={consentConfirmed}
            onChange={(e) => setConsentConfirmed(e.target.checked)}
            style={{ marginTop: '0.2rem', accentColor: 'var(--accent-primary)', cursor: 'pointer' }}
          />
          <label htmlFor="consent-check" style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', cursor: 'pointer', lineHeight: 1.4 }}>
            <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '0.2rem' }}>
              <ShieldCheck size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} />
              Consent & Governance Gate (EPB §7.7.1)
            </strong>
            I confirm active opt-in consent for recording classroom audio, video, and whiteboard feeds.
          </label>
        </div>

        {/* Metadata Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
          <div>
            <label className="form-label">Course Code / Name</label>
            <input
              className="form-input"
              value={courseName}
              onChange={(e) => setCourseName(e.target.value)}
              disabled={recordingState === 'RECORDING'}
              placeholder="e.g. CS101 — Data Structures"
            />
          </div>

          <div>
            <label className="form-label">Lecture Title / Topic</label>
            <input
              className="form-input"
              value={lectureTitle}
              onChange={(e) => setLectureTitle(e.target.value)}
              disabled={recordingState === 'RECORDING'}
              placeholder="e.g. Binary Search Trees"
            />
          </div>

          <div>
            <label className="form-label">Faculty Name</label>
            <input
              className="form-input"
              value={facultyName}
              onChange={(e) => setFacultyName(e.target.value)}
              disabled={recordingState === 'RECORDING'}
              placeholder="e.g. Dr. Alan Turing"
            />
          </div>

          <div>
            <label className="form-label">Classroom / Room Number</label>
            <input
              className="form-input"
              value={classroom}
              onChange={(e) => setClassroom(e.target.value)}
              disabled={recordingState === 'RECORDING'}
              placeholder="e.g. Room 302"
            />
          </div>

          {/* Hardware Device Pickers */}
          {videoDevices.length > 1 && (
            <div>
              <label className="form-label">Camera Device</label>
              <select className="form-select" value={selectedVideoDevice} onChange={(e) => setSelectedVideoDevice(e.target.value)}>
                {videoDevices.map((d) => (
                  <option key={d.deviceId} value={d.deviceId}>
                    {d.label || `Camera ${d.deviceId.slice(0, 5)}`}
                  </option>
                ))}
              </select>
            </div>
          )}

          {audioDevices.length > 1 && (
            <div>
              <label className="form-label">Microphone Device</label>
              <select className="form-select" value={selectedAudioDevice} onChange={(e) => setSelectedAudioDevice(e.target.value)}>
                {audioDevices.map((d) => (
                  <option key={d.deviceId} value={d.deviceId}>
                    {d.label || `Microphone ${d.deviceId.slice(0, 5)}`}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
