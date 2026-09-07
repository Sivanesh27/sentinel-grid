import React, { useState, useEffect } from 'react';
import { Shield, Radio, Sliders, Clock, Activity, AlertTriangle } from 'lucide-react';

export function Header({ connected, threatLevel, cameraCount, onOpenConfig }) {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-GB', { hour12: false }) + ' IST');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getThreatClass = () => {
    switch (threatLevel) {
      case 'CRITICAL':
        return 'threat-critical';
      case 'ELEVATED':
        return 'threat-elevated';
      default:
        return 'threat-low';
    }
  };

  return (
    <header className="top-header">
      <div className="logo-section">
        <Shield className="logo-icon" />
        <div>
          <div className="system-title">
            SENTINEL GRID
            <span className="badge-tag">SIH 2026 // PS 26187</span>
          </div>
          <div style={{ fontSize: '11px', color: '#64748b', letterSpacing: '0.05em' }}>
            AUTONOMOUS BORDER CCTV VIDEO ANALYTICS & FUSION PLATFORM
          </div>
        </div>
      </div>

      <div className="header-status-group">
        {/* Threat Level */}
        <div className={`threat-meter ${getThreatClass()}`}>
          <span className="pulse-dot"></span>
          <span>THREAT STATUS: {threatLevel}</span>
        </div>

        {/* WebSocket Stream Status */}
        <div className="telemetry-item">
          <span className="telemetry-label">STREAM LINK</span>
          <span className="telemetry-value" style={{ color: connected ? '#10b981' : '#ef4444', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Radio size={14} className={connected ? 'pulse-dot' : ''} />
            {connected ? 'ONLINE (15 FPS)' : 'DISCONNECTED'}
          </span>
        </div>

        {/* System Time */}
        <div className="telemetry-item">
          <span className="telemetry-label">SYSTEM TIME</span>
          <span className="telemetry-value" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={14} color="#00f0ff" />
            {timeStr}
          </span>
        </div>

        {/* Fusion Config Button */}
        <button className="btn-tactical" onClick={onOpenConfig} style={{ padding: '6px 12px', fontSize: '12px' }}>
          <Sliders size={14} color="#f59e0b" />
          FUSION WEIGHTS
        </button>
      </div>
    </header>
  );
}
