import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { CameraTile } from './components/CameraTile';
import { AlertFeed } from './components/AlertFeed';
import { AlertDetail } from './components/AlertDetail';
import { ConfigModal } from './components/ConfigModal';
import { FenceEditorModal } from './components/FenceEditorModal';
import { useAlertSocket } from './hooks/useAlertSocket';
import { getApiUrl } from './config';
import { Shield, Eye, ShieldAlert, Cpu, Activity } from 'lucide-react';

export function App() {
  const [cameras, setCameras] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [editingFenceCamera, setEditingFenceCamera] = useState(null);

  const {
    connected,
    frames,
    alerts,
    threatLevel,
    acknowledgeAlert,
    clearAlerts
  } = useAlertSocket();

  // Load camera configurations
  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const res = await fetch(getApiUrl('/api/cameras'));
        if (res.ok) {
          const data = await res.json();
          setCameras(data);
        }
      } catch (err) {
        console.warn('Failed to load cameras list:', err);
      }
    };
    fetchCameras();
    const interval = setInterval(fetchCameras, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle Night Mode CLAHE toggle per camera
  const handleToggleNightMode = async (cameraId, enabled) => {
    try {
      const res = await fetch(getApiUrl(`/api/cameras/${cameraId}/night_mode`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
      if (res.ok) {
        const data = await res.json();
        setCameras((prev) =>
          prev.map((c) => (c.id === cameraId ? { ...c, night_mode: data.night_mode } : c))
        );
      }
    } catch (e) {
      console.error('Failed to toggle night mode:', e);
    }
  };

  // Handle saving updated fence polygon
  const handleSaveFence = (cameraId, updatedFence) => {
    setCameras((prev) =>
      prev.map((c) => (c.id === cameraId ? { ...c, fence: updatedFence } : c))
    );
  };

  // Calculate live summary stats
  const totalTargets = Object.values(frames).reduce((acc, f) => acc + (f?.active_tracks || 0), 0);
  const avgFps = Object.values(frames).length > 0
    ? (Object.values(frames).reduce((acc, f) => acc + (f?.fps || 0), 0) / Object.values(frames).length).toFixed(1)
    : '15.0';

  return (
    <div className="app-container hud-grid">
      {/* Header */}
      <Header
        connected={connected}
        threatLevel={threatLevel}
        cameraCount={cameras.length}
        onOpenConfig={() => setShowConfigModal(true)}
      />

      {/* Main Command Dashboard Layout */}
      <main className="dashboard-grid">
        {/* Left Column: Live Camera Matrix */}
        <section className="camera-section">
          {/* Tactical Status Banner */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#090f1d', border: '1px solid #1e293b', borderRadius: '4px', padding: '8px 16px' }}>
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
              <span className="mono" style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Shield size={14} color="#10b981" />
                FEEDS ARMED: <strong style={{ color: '#f8fafc' }}>{cameras.length}</strong>
              </span>

              <span className="mono" style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Eye size={14} color="#00f0ff" />
                ACTIVE TARGETS: <strong style={{ color: totalTargets > 0 ? '#f59e0b' : '#10b981' }}>{totalTargets}</strong>
              </span>

              <span className="mono" style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Activity size={14} color="#a855f7" />
                SURVEILLANCE ENGINE FPS: <strong style={{ color: '#f8fafc' }}>{avgFps}</strong>
              </span>
            </div>

            <div className="mono" style={{ fontSize: '11px', color: '#64748b' }}>
              PROTOCOL: BYTETRACK // COCO-YOLOV8 // SHAPELY DRAG-DROP FENCE
            </div>
          </div>

          {/* Camera Grid Tiles */}
          <div className="camera-grid">
            {cameras.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
                INITIALIZING SURVEILLANCE MATRIX...
              </div>
            ) : (
              cameras.map((cam) => (
                <CameraTile
                  key={cam.id}
                  camera={cam}
                  frameData={frames[cam.id]}
                  onToggleNightMode={handleToggleNightMode}
                  onEditFence={(c) => setEditingFenceCamera(c)}
                />
              ))
            )}
          </div>
        </section>

        {/* Right Column: Live Alert Feed */}
        <aside>
          <AlertFeed
            alerts={alerts}
            onSelectAlert={(alert) => setSelectedAlert(alert)}
            onClearAlerts={clearAlerts}
          />
        </aside>
      </main>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <AlertDetail
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onAcknowledge={acknowledgeAlert}
        />
      )}

      {/* Fusion Rules & Weights Config Modal */}
      {showConfigModal && (
        <ConfigModal
          onClose={() => setShowConfigModal(false)}
        />
      )}

      {/* Interactive Drag & Drop Virtual Fence Editor Modal */}
      {editingFenceCamera && (
        <FenceEditorModal
          camera={editingFenceCamera}
          frameData={frames[editingFenceCamera.id]}
          onClose={() => setEditingFenceCamera(null)}
          onSaveFence={handleSaveFence}
        />
      )}
    </div>
  );
}

export default App;
