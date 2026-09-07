import React, { useState, useEffect } from 'react';
import { X, Sliders, Save, RotateCcw, CheckCircle2 } from 'lucide-react';
import { getApiUrl } from '../config';

export function ConfigModal({ onClose }) {
  const [weights, setWeights] = useState({
    zone_breach_inbound: 40,
    zone_breach_outbound: 15,
    dwell_time_per_10s: 8,
    group_size_per_person: 6,
    night_time_multiplier: 1.3,
    low_confidence_penalty: -15
  });
  const [alertThreshold, setAlertThreshold] = useState(55);
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState(false);

  useEffect(() => {
    fetch(getApiUrl('/api/config'))
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          if (data.weights) setWeights(data.weights);
          if (data.alert_threshold !== undefined) setAlertThreshold(data.alert_threshold);
        }
      })
      .catch((err) => console.warn('Error loading config:', err));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch(getApiUrl('/api/config'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          weights,
          alert_threshold: alertThreshold
        })
      });
      if (res.ok) {
        setSavedMsg(true);
        setTimeout(() => setSavedMsg(false), 2500);
      }
    } catch (e) {
      console.error('Failed to save config:', e);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setWeights({
      zone_breach_inbound: 40,
      zone_breach_outbound: 15,
      dwell_time_per_10s: 8,
      group_size_per_person: 6,
      night_time_multiplier: 1.3,
      low_confidence_penalty: -15
    });
    setAlertThreshold(55);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={18} color="#f59e0b" />
            <span style={{ fontWeight: 700, fontSize: '15px' }}>
              FUSION RISK ENGINE RULES CONFIGURATION
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
            Sentinel Grid uses a <strong>Trust-Weighted Rule Engine</strong> instead of a black-box model. Adjust weights below to calibrate real-time threat sensitivity. Changes apply immediately to all active feeds.
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '6px' }}>
            {/* Alert Threshold */}
            <div style={{ background: 'rgba(239, 68, 68, 0.05)', padding: '12px', borderRadius: '4px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span className="mono" style={{ fontSize: '12px', color: '#ef4444', fontWeight: 700 }}>
                  ALERT DISPATCH THRESHOLD (SCORE 0-100)
                </span>
                <span className="mono" style={{ fontSize: '14px', fontWeight: 800, color: '#ef4444' }}>
                  {alertThreshold}
                </span>
              </div>
              <input
                type="range"
                min="20"
                max="90"
                step="1"
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: '#ef4444', cursor: 'pointer' }}
              />
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                Scores below threshold are silently logged to SQLite; scores above push live alerts to dashboard.
              </div>
            </div>

            {/* Inbound Breach Weight */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="mono" style={{ fontSize: '12px', color: '#e2e8f0' }}>Inbound Virtual Fence Breach Points</span>
                <span className="mono" style={{ fontWeight: 700, color: '#f59e0b' }}>+{weights.zone_breach_inbound}</span>
              </div>
              <input
                type="range"
                min="0"
                max="60"
                step="1"
                value={weights.zone_breach_inbound}
                onChange={(e) => setWeights({ ...weights, zone_breach_inbound: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
            </div>

            {/* Outbound Breach Weight */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="mono" style={{ fontSize: '12px', color: '#e2e8f0' }}>Outbound Crossing Points</span>
                <span className="mono" style={{ fontWeight: 700, color: '#f59e0b' }}>+{weights.zone_breach_outbound}</span>
              </div>
              <input
                type="range"
                min="0"
                max="40"
                step="1"
                value={weights.zone_breach_outbound}
                onChange={(e) => setWeights({ ...weights, zone_breach_outbound: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
            </div>

            {/* Dwell Time per 10s */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="mono" style={{ fontSize: '12px', color: '#e2e8f0' }}>Dwell Time (Points per 10s in zone)</span>
                <span className="mono" style={{ fontWeight: 700, color: '#f59e0b' }}>+{weights.dwell_time_per_10s}</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                step="1"
                value={weights.dwell_time_per_10s}
                onChange={(e) => setWeights({ ...weights, dwell_time_per_10s: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: '#f59e0b' }}
              />
            </div>

            {/* Group Size Weight */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="mono" style={{ fontSize: '12px', color: '#e2e8f0' }}>Group Density (Points per extra individual)</span>
                <span className="mono" style={{ fontWeight: 700, color: '#38bdf8' }}>+{weights.group_size_per_person}</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                step="1"
                value={weights.group_size_per_person}
                onChange={(e) => setWeights({ ...weights, group_size_per_person: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: '#38bdf8' }}
              />
            </div>

            {/* Night Time Multiplier */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="mono" style={{ fontSize: '12px', color: '#e2e8f0' }}>Night Surveillance Multiplier</span>
                <span className="mono" style={{ fontWeight: 700, color: '#a855f7' }}>{weights.night_time_multiplier}x</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="2.0"
                step="0.05"
                value={weights.night_time_multiplier}
                onChange={(e) => setWeights({ ...weights, night_time_multiplier: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: '#a855f7' }}
              />
            </div>

            {/* Low Confidence Penalty */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span className="mono" style={{ fontSize: '12px', color: '#e2e8f0' }}>Low Confidence Penalty (&lt; 0.5 conf)</span>
                <span className="mono" style={{ fontWeight: 700, color: '#64748b' }}>{weights.low_confidence_penalty}</span>
              </div>
              <input
                type="range"
                min="-30"
                max="0"
                step="1"
                value={weights.low_confidence_penalty}
                onChange={(e) => setWeights({ ...weights, low_confidence_penalty: parseFloat(e.target.value) })}
                style={{ width: '100%', accentColor: '#64748b' }}
              />
            </div>
          </div>
        </div>

        <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
          <button className="btn-tactical" onClick={handleReset}>
            <RotateCcw size={13} />
            RESET DEFAULTS
          </button>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {savedMsg && (
              <span className="mono" style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={13} /> WEIGHTS SAVED
              </span>
            )}
            <button
              className="btn-tactical"
              style={{ background: '#0284c7', borderColor: '#38bdf8', color: '#fff' }}
              onClick={handleSave}
              disabled={saving}
            >
              <Save size={13} />
              {saving ? 'SAVING...' : 'APPLY WEIGHTS'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
