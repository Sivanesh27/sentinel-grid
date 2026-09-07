import React from 'react';
import { X, AlertTriangle, ShieldAlert, CheckCircle, Clock, MapPin, Car, Users, Zap } from 'lucide-react';

export function AlertDetail({ alert, onClose, onAcknowledge }) {
  if (!alert) return null;

  const getSeverityBadgeClass = (sev) => {
    switch (sev) {
      case 'CRITICAL':
        return 'badge-critical';
      case 'HIGH':
        return 'badge-high';
      case 'MEDIUM':
        return 'badge-medium';
      default:
        return 'badge-low';
    }
  };

  const breakdown = alert.factor_breakdown || (alert.details ? JSON.parse(alert.details) : {});

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert size={20} color={alert.risk_score >= 80 ? '#ef4444' : '#f59e0b'} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '15px', color: '#f8fafc' }}>
                SECURITY INCIDENT: {alert.alert_id}
              </div>
              <div className="mono" style={{ fontSize: '11px', color: '#64748b' }}>
                CAMERA: {alert.camera_name || alert.camera_id} // TRACK ID: #{alert.track_id}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Top Score Banner */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#090f1d', padding: '14px 18px', borderRadius: '6px', border: '1px solid #1e293b' }}>
            <div>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }} className="mono">
                COMPOSITE RISK ASSESSMENT
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
                <span className="mono" style={{ fontSize: '32px', fontWeight: 800, color: alert.risk_score >= 80 ? '#ef4444' : '#f59e0b' }}>
                  {alert.risk_score}
                </span>
                <span className="mono" style={{ color: '#64748b', fontSize: '14px' }}>/ 100</span>
                <span className={`alert-score-badge ${getSeverityBadgeClass(alert.severity)}`} style={{ marginLeft: '12px' }}>
                  {alert.severity} THREAT
                </span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: '#64748b' }} className="mono">DETECTION TIMESTAMP</div>
              <div className="mono" style={{ fontSize: '13px', color: '#e2e8f0', marginTop: '4px' }}>
                {new Date(alert.timestamp).toLocaleString('en-GB')}
              </div>
            </div>
          </div>

          {/* Natural Language Narrative Explanation */}
          <div style={{ background: 'rgba(2, 132, 199, 0.08)', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '14px', borderRadius: '6px' }}>
            <div className="mono" style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 700, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Zap size={14} /> FUSION ENGINE EXPLANATION NARRATIVE:
            </div>
            <div style={{ fontSize: '14px', color: '#f1f5f9', fontStyle: 'italic', lineHeight: 1.4 }}>
              "{alert.explanation}"
            </div>
          </div>

          {/* Snapshot Preview */}
          {alert.snapshot && (
            <div>
              <div className="mono" style={{ fontSize: '11px', color: '#64748b', marginBottom: '6px' }}>
                INCIDENT SNAPSHOT CAPTURE:
              </div>
              <div className="snapshot-container">
                <img src={alert.snapshot} alt="Breach snapshot" className="snapshot-img" />
              </div>
            </div>
          )}

          {/* Trust-Weighted Factor Breakdown Grid */}
          <div>
            <div className="mono" style={{ fontSize: '11px', color: '#64748b', marginBottom: '8px' }}>
              TRUST-WEIGHTED RULE FACTOR BREAKDOWN:
            </div>
            <div className="factor-grid">
              <div className="factor-item">
                <span className="factor-name">Zone Breach</span>
                <span className="factor-value" style={{ color: '#ef4444' }}>
                  +{breakdown.zone_breach_points || 0} pts
                </span>
              </div>

              <div className="factor-item">
                <span className="factor-name">Dwell Duration</span>
                <span className="factor-value" style={{ color: '#f59e0b' }}>
                  +{breakdown.dwell_time_points || 0} pts ({breakdown.dwell_seconds || 0}s)
                </span>
              </div>

              <div className="factor-item">
                <span className="factor-name">Group Size</span>
                <span className="factor-value" style={{ color: '#38bdf8' }}>
                  +{breakdown.group_size_points || 0} pts ({breakdown.group_size || 1} people)
                </span>
              </div>

              <div className="factor-item">
                <span className="factor-name">Night Multiplier</span>
                <span className="factor-value" style={{ color: breakdown.is_night_time ? '#a855f7' : '#94a3b8' }}>
                  {breakdown.night_multiplier || 1.0}x
                </span>
              </div>

              {breakdown.plate_number && (
                <div className="factor-item" style={{ gridColumn: 'span 2' }}>
                  <span className="factor-name">ANPR License Plate</span>
                  <span className="factor-value" style={{ color: '#10b981' }}>
                    [{breakdown.plate_number}]
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-tactical" onClick={onClose}>
            CLOSE
          </button>
          {!alert.acknowledged && (
            <button
              className="btn-tactical"
              style={{ background: 'rgba(16, 185, 129, 0.2)', borderColor: '#10b981', color: '#10b981' }}
              onClick={() => {
                onAcknowledge(alert.alert_id);
                onClose();
              }}
            >
              <CheckCircle size={14} />
              ACKNOWLEDGE INCIDENT
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
