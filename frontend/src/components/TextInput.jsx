import React from 'react';

export default function TextInput({ value, onChange }) {
  return (
    <div className="card">
      <div className="card__header">
        <span className="card__icon">💬</span>
        <h2 className="card__title">Describe Your Emergency</h2>
      </div>
      <textarea
        id="emergency-text-input"
        className="text-input__textarea"
        placeholder="Describe symptoms, injuries, or the emergency situation in detail... (e.g., 'severe chest pain radiating to left arm, sweating heavily')"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={5}
      />
    </div>
  );
}
