import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileVideo,
  FileAudio,
  FileText,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowRight,
  X,
  FileUp,
} from 'lucide-react';
import { api } from '../services/api';

export default function LectureUploader({ onUploadComplete }) {
  // Form State
  const [courseName, setCourseName] = useState('CS202 - Database Management Systems');
  const [facultyName, setFacultyName] = useState('Dr. Grace Hopper');
  const [lectureTitle, setLectureTitle] = useState('Relational Algebra & Normalization');
  const [classroom, setClassroom] = useState('Lecture Hall 1');
  const [lectureDate, setLectureDate] = useState(new Date().toISOString().split('T')[0]);

  // Selected Files
  const [mediaFile, setMediaFile] = useState(null);
  const [slidesFile, setSlidesFile] = useState(null);

  // Upload Status
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [resultMessage, setResultMessage] = useState(null);

  const mediaInputRef = useRef(null);
  const slidesInputRef = useRef(null);

  const handleMediaDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setMediaFile(e.dataTransfer.files[0]);
    }
  };

  const handleSlidesDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSlidesFile(e.dataTransfer.files[0]);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!mediaFile && !slidesFile) {
      alert('Please select at least one lecture recording or slide deck file.');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(20);
      setResultMessage(null);

      const formData = new FormData();
      formData.append('course_name_or_code', courseName);
      formData.append('faculty_name', facultyName);
      formData.append('title', lectureTitle);
      formData.append('classroom', classroom);
      formData.append('lecture_date', lectureDate);

      if (mediaFile) {
        const isVideo = mediaFile.type.startsWith('video/') || mediaFile.name.match(/\.(mp4|webm|mkv|mov|avi)$/i);
        if (isVideo) {
          formData.append('video_file', mediaFile);
        } else {
          formData.append('audio_file', mediaFile);
        }
      }

      if (slidesFile) {
        formData.append('slides_file', slidesFile);
      }

      setUploadProgress(50);
      const res = await api.uploadLecturePackage(formData);
      setUploadProgress(100);

      setResultMessage({
        type: 'success',
        title: 'Lecture Ingested Successfully!',
        data: res,
      });

      // Clear files
      setMediaFile(null);
      setSlidesFile(null);

      if (onUploadComplete) onUploadComplete(res);
    } catch (err) {
      setResultMessage({
        type: 'error',
        title: 'Upload Failed',
        message: err.message,
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', marginBottom: '0.35rem' }}>Upload Pre-Recorded Lecture & Slides</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Upload classroom video/audio recordings and presentation slide decks (.pptx / .pdf). The backend automatically normalizes audio to 16kHz mono WAV and parses slide keyframes for AI intelligence.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          {/* Metadata Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
            <div>
              <label className="form-label">Course Code / Name</label>
              <input
                className="form-input"
                value={courseName}
                onChange={(e) => setCourseName(e.target.value)}
                required
                placeholder="e.g. CS202 — Database Systems"
              />
            </div>

            <div>
              <label className="form-label">Faculty / Instructor</label>
              <input
                className="form-input"
                value={facultyName}
                onChange={(e) => setFacultyName(e.target.value)}
                required
                placeholder="e.g. Dr. Grace Hopper"
              />
            </div>

            <div>
              <label className="form-label">Lecture Topic / Title</label>
              <input
                className="form-input"
                value={lectureTitle}
                onChange={(e) => setLectureTitle(e.target.value)}
                required
                placeholder="e.g. Query Optimization & Indexing"
              />
            </div>

            <div>
              <label className="form-label">Classroom / Room</label>
              <input
                className="form-input"
                value={classroom}
                onChange={(e) => setClassroom(e.target.value)}
                placeholder="e.g. Hall 101"
              />
            </div>

            <div>
              <label className="form-label">Lecture Date</label>
              <input
                type="date"
                className="form-input"
                value={lectureDate}
                onChange={(e) => setLectureDate(e.target.value)}
              />
            </div>
          </div>

          {/* Dual Dropzones: Media & Slides */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            {/* Media Dropzone */}
            <div>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <FileVideo size={15} color="var(--accent-primary)" />
                Lecture Recording (Video / Audio)
              </label>

              <input
                type="file"
                ref={mediaInputRef}
                style={{ display: 'none' }}
                accept="video/*,audio/*,.mkv"
                onChange={(e) => e.target.files && setMediaFile(e.target.files[0])}
              />

              {!mediaFile ? (
                <div
                  className="dropzone"
                  onClick={() => mediaInputRef.current.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleMediaDrop}
                >
                  <UploadCloud size={32} color="var(--accent-primary)" style={{ margin: '0 auto 0.75rem' }} />
                  <p style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>Click or drag recording here</p>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MP4, WebM, MKV, WAV, MP3</span>
                </div>
              ) : (
                <div
                  style={{
                    padding: '1.25rem',
                    background: 'var(--bg-secondary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-highlight)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-sm)', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--accent-primary)' }}>
                      <FileVideo size={20} />
                    </div>
                    <div>
                      <p style={{ fontSize: '0.88rem', fontWeight: 600 }}>{mediaFile.name}</p>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatFileSize(mediaFile.size)}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setMediaFile(null)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  >
                    <X size={18} />
                  </button>
                </div>
              )}
            </div>

            {/* Slides Dropzone */}
            <div>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <FileText size={15} color="var(--accent-secondary)" />
                Presentation Deck (PPTX / PDF)
              </label>

              <input
                type="file"
                ref={slidesInputRef}
                style={{ display: 'none' }}
                accept=".pptx,.ppt,.pdf"
                onChange={(e) => e.target.files && setSlidesFile(e.target.files[0])}
              />

              {!slidesFile ? (
                <div
                  className="dropzone"
                  onClick={() => slidesInputRef.current.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleSlidesDrop}
                >
                  <FileUp size={32} color="var(--accent-secondary)" style={{ margin: '0 auto 0.75rem' }} />
                  <p style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>Click or drag slide deck</p>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PPTX, PPT, or PDF slides</span>
                </div>
              ) : (
                <div
                  style={{
                    padding: '1.25rem',
                    background: 'var(--bg-secondary)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid rgba(139, 92, 246, 0.35)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-sm)', background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-secondary)' }}>
                      <FileText size={20} />
                    </div>
                    <div>
                      <p style={{ fontSize: '0.88rem', fontWeight: 600 }}>{slidesFile.name}</p>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatFileSize(slidesFile.size)}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSlidesFile(null)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  >
                    <X size={18} />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Upload Progress Bar */}
          {uploading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                <span>Uploading and extracting 16kHz audio...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="vu-meter-bar" style={{ height: '6px' }}>
                <div className="vu-meter-fill" style={{ width: `${uploadProgress}%`, background: 'var(--accent-primary)' }} />
              </div>
            </div>
          )}

          {/* Result Alert */}
          {resultMessage && (
            <div
              style={{
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                background: resultMessage.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
                border: `1px solid ${resultMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                color: resultMessage.type === 'success' ? '#34d399' : '#fb7185',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.85rem',
              }}
            >
              {resultMessage.type === 'success' ? <CheckCircle2 size={20} style={{ flexShrink: 0, marginTop: '2px' }} /> : <AlertCircle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />}
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: '0.95rem', marginBottom: '0.35rem', color: 'inherit' }}>{resultMessage.title}</h4>
                {resultMessage.type === 'success' ? (
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Session ID: <strong style={{ color: 'var(--text-primary)' }}>{resultMessage.data.session_id}</strong>
                    {resultMessage.data.has_extracted_audio && ' • 16kHz Mono WAV extracted for Whisper STT'}
                    {resultMessage.data.slide_count > 0 && ` • ${resultMessage.data.slide_count} slides extracted`}
                  </p>
                ) : (
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{resultMessage.message}</p>
                )}
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={uploading || (!mediaFile && !slidesFile)}
            style={{ padding: '0.9rem', fontSize: '1rem', marginTop: '0.5rem' }}
          >
            <UploadCloud size={18} />
            {uploading ? 'Processing & Ingesting Media...' : 'Upload & Process Lecture Package'}
          </button>
        </form>
      </div>
    </div>
  );
}
