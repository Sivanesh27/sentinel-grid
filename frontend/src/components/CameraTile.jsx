import React from 'react';
import { Video, ShieldCheck, Eye, Layers, Edit3 } from 'lucide-react';
import { NightModeToggle } from './NightModeToggle';

export function CameraTile({ camera, frameData, onToggleNightMode, onEditFence }) {
  const imageSrc = frameData?.image;
  const fps = frameData?.fps || camera.fps || 15;
  const activeTracks = frameData?.active_tracks || 0;

  return (
    <div className="camera-card">
      <div className="camera-header">
        <div className="camera-title-group">
          <Video size={15} color="#38bdf8" />
          <span className="camera-name">{camera.name.toUpperCase()}</span>
          <span className="badge-tag" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
            [ID: {camera.id.toUpperCase()}]
          </span>
        </div>

        <div className="camera-controls">
          <button
            className="btn-tactical"
            onClick={() => onEditFence(camera)}
            title="Drag & Drop Virtual Fence Editor"
            style={{ borderColor: 'rgba(0, 240, 255, 0.4)', color: '#00f0ff' }}
          >
            <Edit3 size={12} color="#00f0ff" />
            <span>EDIT FENCE</span>
          </button>

          <NightModeToggle
            cameraId={camera.id}
            nightMode={camera.night_mode}
            onToggle={onToggleNightMode}
          />
        </div>
      </div>

      <div className="video-container">
        {imageSrc ? (
          <img
            src={imageSrc}
            alt={camera.name}
            className="video-frame"
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: '#64748b' }}>
            <Eye size={32} className="pulse-dot" />
            <span className="mono" style={{ fontSize: '12px' }}>AWAITING SENSOR STREAM...</span>
          </div>
        )}
      </div>

      <div className="camera-footer">
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Layers size={12} color="#00f0ff" />
          TARGETS: <strong style={{ color: activeTracks > 0 ? '#f59e0b' : '#94a3b8' }}>{activeTracks}</strong>
        </span>

        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          FPS: <strong style={{ color: '#e2e8f0' }}>{fps}</strong>
        </span>

        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <ShieldCheck size={12} color="#10b981" />
          FENCE: {camera.fence?.name || 'ARMED'}
        </span>
      </div>
    </div>
  );
}
