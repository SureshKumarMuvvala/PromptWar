import React from 'react';

export default function ActionPanel({ result }) {
  if (!result) {
    return (
      <div className="card">
        <div className="empty-state">
          <span className="empty-state__icon">🏥</span>
          <p className="empty-state__text">
            Submit your emergency information to receive an AI-powered triage assessment and recommended actions.
          </p>
        </div>
      </div>
    );
  }

  const { structured_assessment, rag_validation, recommended_actions } = result;

  return (
    <div className="action-panel">
      {/* ── Assessment Summary ──────────────────────────────── */}
      <div className="card">
        <div className="card__header">
          <span className="card__icon">🩺</span>
          <h2 className="card__title">Assessment</h2>
        </div>

        <div className="assessment-summary">
          <span className="assessment-summary__complaint">
            {structured_assessment.chief_complaint}
          </span>
          <span className={`severity-badge severity-badge--${structured_assessment.severity}`}>
            ⚠ {structured_assessment.severity}
          </span>
          <div className="triage-indicator">
            <span className={`triage-dot triage-dot--${structured_assessment.triage_level}`} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Triage: {structured_assessment.triage_level}
            </span>
          </div>
        </div>

        {/* Symptoms */}
        {structured_assessment.symptoms?.length > 0 && (
          <>
            <hr className="divider" />
            <p className="section-label">Symptoms</p>
            <div className="symptom-tags">
              {structured_assessment.symptoms.map((s, i) => (
                <span key={i} className="symptom-tag">{s}</span>
              ))}
            </div>
          </>
        )}

        {/* Conditions */}
        {structured_assessment.possible_conditions?.length > 0 && (
          <>
            <hr className="divider" />
            <p className="section-label">Possible Conditions</p>
            <ul className="condition-list">
              {structured_assessment.possible_conditions.map((c, i) => (
                <li key={i} className="condition-item">
                  <span className="condition-item__name">{c.name}</span>
                  <div className="condition-item__meta">
                    <span>ICD-10: {c.icd10}</span>
                    <span className="condition-item__confidence">
                      {Math.round(c.confidence * 100)}%
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      {/* ── RAG Validation ─────────────────────────────────── */}
      {rag_validation && (
        <div className="card">
          <div className="card__header">
            <span className="card__icon">🔍</span>
            <h2 className="card__title">Clinical Validation (RAG)</h2>
          </div>
          <div className="rag-section">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem' }}>
                {rag_validation.validated ? '✅ Validated' : '⚠️ Corrections Applied'}
              </span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Confidence: {Math.round(rag_validation.confidence_score * 100)}%
              </span>
            </div>
            {rag_validation.matched_protocols?.length > 0 && (
              <div className="rag-protocols">
                {rag_validation.matched_protocols.map((p, i) => (
                  <span key={i} className="rag-protocol-tag">{p}</span>
                ))}
              </div>
            )}
            {rag_validation.corrections?.map((c, i) => (
              <div key={i} className="rag-correction">
                <strong>{c.field}:</strong> {c.original} → {c.corrected}
                <br />
                <em>{c.reason}</em>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Recommended Actions ────────────────────────────── */}
      {recommended_actions?.length > 0 && (
        <div className="card">
          <div className="card__header">
            <span className="card__icon">🚨</span>
            <h2 className="card__title">Recommended Actions</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            {recommended_actions.map((action, i) => (
              <div key={i} className={`action-card action-card--${action.type}`}>
                <div className="action-card__header">
                  <span className="action-card__type">
                    {action.type.replace(/_/g, ' ')}
                  </span>
                  <span className="action-card__priority">P{action.priority}</span>
                </div>
                <p className="action-card__description">{action.description}</p>
                {action.auto_triggered && (
                  <span className="action-card__auto">⚡ Auto-triggered</span>
                )}
                {action.hospitals?.length > 0 && (
                  <div style={{ marginTop: 'var(--space-sm)' }}>
                    {action.hospitals.map((h, j) => (
                      <div key={j} className="hospital-item">
                        <div>
                          <div className="hospital-item__name">{h.name}</div>
                          <div className="hospital-item__details">{h.address}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          {h.distance_km && (
                            <div className="hospital-item__details">{h.distance_km} km</div>
                          )}
                          {h.phone && (
                            <a href={`tel:${h.phone}`} style={{ fontSize: '0.8rem', color: 'var(--accent-primary)' }}>
                              {h.phone}
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
