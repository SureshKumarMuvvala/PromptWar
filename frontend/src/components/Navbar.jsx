import React from 'react';

export default function Navbar({ isOnline }) {
  return (
    <nav className="navbar">
      <div className="navbar__brand">
        <span className="navbar__icon">🚑</span>
        <h1 className="navbar__title">Emergency Health Assistant</h1>
      </div>
      <div className="navbar__status">
        <span className={`navbar__status-dot ${isOnline ? '' : 'navbar__status-dot--offline'}`} />
        {isOnline ? 'System Online' : 'Connecting...'}
      </div>
    </nav>
  );
}
