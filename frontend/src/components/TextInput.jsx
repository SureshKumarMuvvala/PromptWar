import React from 'react';

export default function TextInput({ value, onChange }) {
  return (
    <div className="card">
      <div className="card__header">
        <span className="card__icon" role="img" aria-label="Chat icon">💬</span>
        <h2 className="card__title" id="text-input-title">Describe Your Emergency</h2>
      </div>
      <label htmlFor="emergency-text-input" className="sr-only">Detailed description of symptoms or injuries</label>
      <textarea
        id="emergency-text-input"
        className="text-input__textarea"
        aria-labelledby="text-input-title"
        aria-required="true"
        placeholder="Describe symptoms, injuries, or the emergency situation in detail... (e.g., 'severe chest pain radiating to left arm, sweating heavily')"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={5}
      />
    </div>
  );
}
