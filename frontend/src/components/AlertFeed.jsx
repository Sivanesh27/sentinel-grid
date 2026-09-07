import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, Filter, Trash2, ChevronRight, Eye } from 'lucide-react';

export function AlertFeed({ alerts, onSelectAlert, onClearAlerts }) {
  const [filter, setFilter] = useState('ALL');

  const filteredAlerts = alerts.filter((a) => {
    if (filter === 'CRITICAL') return a.risk_score >= 80;
    if (filter === 'HIGH') return a.risk_score >= 60 && a.risk_score < 80;
    if (filter === 'VEHICLE') return a.class_name === 'car' || a.class_name === 'truck' || a.class_name === 'bus';
    return true;
  });

  const getAlertCardClass = (score) => {
    if (score >= 80) return 'alert-card critical';
    if (score >= 60) return 'alert-card high';
    return 'alert-card medium';
  };

  const getBadgeClass = (sev) => {
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

  return (
    <div className="alert-feed-panel">
      <div className="panel-header">
        <div className="panel-title">
          <ShieldAlert size={18} color="#ef4444" />
          <span>SECURITY ALERTS</span>
          <span className="alert-counter-badge">{alerts.length}</span>
        </div>

        {alerts.length > 0 && (
          <button
            onClick={onClearAlerts}
            className="btn-tactical"
            style={{ padding: '3px 8px', fontSize: '10px' }}
            title="Clear current alert buffer"
          >
            <Trash2 size={11} />
            CLEAR
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '6px', padding: '8px 12px', background: '#090f1d', borderBottom: '1px solid #1e293b' }}>
        {['ALL', 'CRITICAL', 'HIGH', 'VEHICLE'].map((tab) => (
          <button
            key={tab}
            className={`btn-tactical ${filter === tab ? 'active-night' : ''}`}
            style={{ padding: '3px 8px', fontSize: '10px', flex: 1, justifyContent: 'center' }}
            onClick={() => setFilter(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Scrolling List */}
      <div className="alert-list">
        {filteredAlerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
            <AlertTriangle size={28} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
            <div className="mono" style={{ fontSize: '12px' }}>NO ACTIVE INCIDENTS</div>
            <div style={{ fontSize: '11px', marginTop: '4px' }}>Surveillance grid secure. Low-risk movements logged to SQLite.</div>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.alert_id || alert.id}
              className={getAlertCardClass(alert.risk_score)}
              onClick={() => onSelectAlert(alert)}
            >
              <div className="alert-card-top">
                <span className="alert-cam-tag">
                  [{alert.camera_id?.toUpperCase() || 'CAM'}] // TRK #{alert.track_id}
                </span>
                <span className={`alert-score-badge ${getBadgeClass(alert.severity)}`}>
                  RISK: {alert.risk_score}
                </span>
              </div>

              <div className="alert-explanation">
                {alert.explanation}
              </div>

              <div className="alert-footer">
                <span>{new Date(alert.timestamp).toLocaleTimeString('en-GB')}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '2px', color: '#38bdf8' }}>
                  INSPECT <ChevronRight size={12} />
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
