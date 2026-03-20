import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import TextInput from './components/TextInput';
import VoiceRecorder from './components/VoiceRecorder';
import ImageUploader from './components/ImageUploader';
import ActionPanel from './components/ActionPanel';
import { assessEmergency, checkStatus } from './services/api';
import { getUserLocation } from './utils/mediaHelpers';

export default function App() {
  const [text, setText] = useState('');
  const [audio, setAudio] = useState(null);
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isOnline, setIsOnline] = useState(false);

  // Health check on mount
  useEffect(() => {
    checkStatus()
      .then(() => setIsOnline(true))
      .catch(() => setIsOnline(false));
  }, []);

  const hasInput = text.trim() || audio || image;

  const handleSubmit = useCallback(async () => {
    if (!hasInput || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Try to get location
      let latitude = null;
      let longitude = null;
      try {
        const loc = await getUserLocation();
        latitude = loc.latitude;
        longitude = loc.longitude;
      } catch {
        // Location not available — continue without it
      }

      const data = await assessEmergency({
        text: text.trim() || null,
        audio,
        image,
        latitude,
        longitude,
      });

      setResult(data);
      setIsOnline(true);
    } catch (err) {
      console.error('Assessment failed:', err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to assess emergency. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, [text, audio, image, hasInput, loading]);

  return (
    <div className="app">
      <Navbar isOnline={isOnline} />

      {error && <div className="error-banner">⚠️ {error}</div>}

      <div className="main-grid">
        {/* ── Left: Input Panel ──────────────────────────────── */}
        <div className="input-section">
          <TextInput value={text} onChange={setText} />
          <VoiceRecorder onRecordingComplete={setAudio} />
          <ImageUploader onImageSelected={setImage} />

          <button
            id="submit-assessment-btn"
            className={`submit-btn ${loading ? 'submit-btn--loading' : ''}`}
            onClick={handleSubmit}
            disabled={!hasInput || loading}
          >
            {loading && <span className="submit-btn__spinner" />}
            {loading ? 'Analyzing Emergency...' : '🚨 Assess Emergency'}
          </button>
        </div>

        {/* ── Right: Results Panel ───────────────────────────── */}
        <div>
          <ActionPanel result={result} />
        </div>
      </div>
    </div>
  );
}
