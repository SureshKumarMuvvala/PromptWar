import React from 'react';

export default function Navbar({ isOnline }) {
  return (
    <header className="navbar" role="banner">
      <div className="navbar__brand">
        <span className="navbar__icon" role="img" aria-label="Ambulance icon">🚑</span>
        <h1 className="navbar__title">Emergency Health Assistant</h1>
      </div>
      <div className="navbar__status" role="status" aria-live="polite">
        <span 
          className={`navbar__status-dot ${isOnline ? '' : 'navbar__status-dot--offline'}`}
          aria-hidden="true" 
        />
        <span className="sr-only">System status: </span>
        {isOnline ? 'System Online' : 'Connecting...'}
      </div>
    </header>
  );
}
