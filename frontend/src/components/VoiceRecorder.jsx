import React, { useState, useRef, useCallback } from 'react';
import { blobToFile } from '../utils/mediaHelpers';

export default function VoiceRecorder({ onRecordingComplete }) {
  const [isRecording, setIsRecording] = useState(false);
  const [hasRecording, setHasRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4',
      });

      chunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType });
        const file = blobToFile(blob, `recording.${mediaRecorder.mimeType.split('/')[1]}`);
        onRecordingComplete(file);
        setHasRecording(true);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(250);
      setIsRecording(true);
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration((d) => d + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Please allow microphone access to use voice input.');
    }
  }, [onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    clearInterval(timerRef.current);
  }, []);

  const formatDuration = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <section className="card" aria-labelledby="voice-input-title">
      <div className="card__header">
        <span className="card__icon" role="img" aria-label="Microphone icon">🎙️</span>
        <h2 className="card__title" id="voice-input-title">Voice Input</h2>
      </div>
      <div className="voice-recorder">
        <button
          id="voice-record-btn"
          className={`voice-recorder__btn ${isRecording ? 'voice-recorder__btn--recording' : ''}`}
          onClick={isRecording ? stopRecording : startRecording}
          type="button"
          aria-pressed={isRecording}
          aria-label={isRecording ? "Stop recording voice" : "Start recording voice"}
        >
          {isRecording ? '⏹ Stop' : '🎤 Record'}
        </button>
        <span className="voice-recorder__status" role="status" aria-live="polite">
          {isRecording
            ? `Recording... ${formatDuration(duration)}`
            : hasRecording
              ? '✅ Recording captured'
              : 'Click to start recording'}
        </span>
      </div>
    </section>
  );
}
