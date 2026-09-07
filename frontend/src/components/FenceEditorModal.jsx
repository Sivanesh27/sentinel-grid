import React, { useState, useRef, useEffect } from 'react';
import { X, Save, RotateCcw, Plus, Trash2, Shield, ArrowDown, ArrowUp, ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react';
import { getApiUrl } from '../config';

export function FenceEditorModal({ camera, frameData, onClose, onSaveFence }) {
  const [polygon, setPolygon] = useState(
    camera.fence?.polygon || [[100, 320], [540, 320], [540, 460], [100, 460]]
  );
  const [fenceName, setFenceName] = useState(camera.fence?.name || 'Virtual Fence');
  const [direction, setDirection] = useState(camera.fence?.inbound_direction || 'down');
  const [draggingIdx, setDraggingIdx] = useState(null);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const svgRef = useRef(null);

  // Convert client coordinate to SVG 640x480 coordinate space
  const getSvgCoordinates = (e) => {
    if (!svgRef.current) return [0, 0];
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

    const scaleX = 640 / rect.width;
    const scaleY = 480 / rect.height;

    const x = Math.max(10, Math.min(630, Math.round((clientX - rect.left) * scaleX)));
    const y = Math.max(10, Math.min(470, Math.round((clientY - rect.top) * scaleY)));

    return [x, y];
  };

  const handleMouseDown = (idx, e) => {
    e.stopPropagation();
    setDraggingIdx(idx);
  };

  const handleMouseMove = (e) => {
    if (draggingIdx === null) return;
    const [x, y] = getSvgCoordinates(e);
    setPolygon((prev) => {
      const next = [...prev];
      next[draggingIdx] = [x, y];
      return next;
    });
  };

  const handleMouseUp = () => {
    setDraggingIdx(null);
  };

  // Add vertex point
  const handleAddPoint = () => {
    if (polygon.length >= 8) return;
    const lastP = polygon[polygon.length - 1];
    const newP = [Math.min(600, lastP[0] + 40), Math.min(450, lastP[1] + 30)];
    setPolygon([...polygon, newP]);
  };

  // Remove last vertex
  const handleRemovePoint = () => {
    if (polygon.length <= 3) return;
    setPolygon(polygon.slice(0, -1));
  };

  // Preset layouts
  const applyPreset = (type) => {
    switch (type) {
      case 'horizontal':
        setPolygon([[80, 300], [560, 300], [560, 440], [80, 440]]);
        break;
      case 'perspective':
        setPolygon([[280, 160], [440, 160], [480, 420], [160, 420]]);
        break;
      case 'left_fence':
        setPolygon([[60, 180], [280, 180], [240, 440], [60, 440]]);
        break;
      case 'checkpoint':
        setPolygon([[100, 270], [540, 270], [540, 390], [100, 390]]);
        break;
      default:
        break;
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch(getApiUrl(`/api/cameras/${camera.id}/fence`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          polygon,
          name: fenceName,
          inbound_direction: direction
        })
      });

      if (res.ok) {
        const data = await res.json();
        setSavedSuccess(true);
        onSaveFence(camera.id, data.fence);
        setTimeout(() => {
          setSavedSuccess(false);
          onClose();
        }, 1200);
      }
    } catch (e) {
      console.error('Failed to save virtual fence:', e);
    } finally {
      setSaving(false);
    }
  };

  // Format points string for SVG polygon
  const polygonPointsStr = polygon.map((p) => `${p[0]},${p[1]}`).join(' ');

  return (
    <div
      className="modal-backdrop"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onTouchMove={handleMouseMove}
      onTouchEnd={handleMouseUp}
    >
      <div className="modal-card" style={{ maxWidth: '820px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={18} color="#00f0ff" />
            <span style={{ fontWeight: 700, fontSize: '15px' }}>
              VIRTUAL FENCE EDITOR // [{camera.name.toUpperCase()}]
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body" style={{ gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>
              <strong>Drag and drop</strong> the circular corner handles directly on the video to align the virtual fence polygon with the physical fence or road.
            </div>

            {/* Inbound Crossing Direction */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="mono" style={{ fontSize: '11px', color: '#64748b' }}>INBOUND HEADING:</span>
              <select
                value={direction}
                onChange={(e) => setDirection(e.target.value)}
                className="btn-tactical"
                style={{ padding: '3px 8px', fontSize: '11px', background: '#090f1d' }}
              >
                <option value="down">Downward (Inward Breach)</option>
                <option value="up">Upward (Inward Breach)</option>
                <option value="right">Rightward</option>
                <option value="left">Leftward</option>
              </select>
            </div>
          </div>

          {/* Interactive Drag & Drop Video Canvas Container */}
          <div
            style={{
              position: 'relative',
              width: '100%',
              aspectRatio: '4 / 3',
              background: '#000',
              borderRadius: '6px',
              overflow: 'hidden',
              border: '1px solid #334155',
              userSelect: 'none'
            }}
          >
            {/* Live Camera Snapshot */}
            {frameData?.image ? (
              <img
                src={frameData.image}
                alt="Camera Frame"
                style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block', pointerEvents: 'none' }}
              />
            ) : (
              <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                LOADING CAMERA FEED...
              </div>
            )}

            {/* SVG Interactive Overlay */}
            <svg
              ref={svgRef}
              viewBox="0 0 640 480"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                cursor: draggingIdx !== null ? 'grabbing' : 'crosshair'
              }}
            >
              {/* Virtual Fence Polygon Fill */}
              <polygon
                points={polygonPointsStr}
                fill="rgba(0, 240, 255, 0.22)"
                stroke="#00f0ff"
                strokeWidth="2"
                strokeDasharray="6 3"
              />

              {/* Vertex Drag Handles */}
              {polygon.map((p, idx) => (
                <g key={idx} transform={`translate(${p[0]}, ${p[1]})`}>
                  {/* Outer Pulsing Ring */}
                  <circle
                    r="14"
                    fill={draggingIdx === idx ? 'rgba(0, 240, 255, 0.4)' : 'rgba(16, 185, 129, 0.3)'}
                    stroke={draggingIdx === idx ? '#00f0ff' : '#10b981'}
                    strokeWidth="2"
                    style={{ cursor: 'grab', transition: 'r 0.1s' }}
                    onMouseDown={(e) => handleMouseDown(idx, e)}
                    onTouchStart={(e) => handleMouseDown(idx, e)}
                  />
                  {/* Center Dot */}
                  <circle
                    r="5"
                    fill="#ffffff"
                    style={{ pointerEvents: 'none' }}
                  />
                  {/* Vertex Label */}
                  <text
                    y="-16"
                    textAnchor="middle"
                    fill="#00f0ff"
                    fontSize="11"
                    fontFamily="monospace"
                    fontWeight="bold"
                    style={{ pointerEvents: 'none', textShadow: '0 0 4px #000' }}
                  >
                    P{idx + 1} ({p[0]},{p[1]})
                  </text>
                </g>
              ))}
            </svg>
          </div>

          {/* Controls & Quick Presets Toolbar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#090f1d', padding: '10px 14px', borderRadius: '4px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="mono" style={{ fontSize: '11px', color: '#64748b' }}>PRESETS:</span>
              <button className="btn-tactical" onClick={() => applyPreset('horizontal')}>Horizontal</button>
              <button className="btn-tactical" onClick={() => applyPreset('perspective')}>Roadway</button>
              <button className="btn-tactical" onClick={() => applyPreset('left_fence')}>Left Fence</button>
              <button className="btn-tactical" onClick={() => applyPreset('checkpoint')}>Checkpoint</button>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                className="btn-tactical"
                onClick={handleAddPoint}
                disabled={polygon.length >= 8}
                title="Add Corner Node"
              >
                <Plus size={13} color="#10b981" />
                ADD NODE ({polygon.length}/8)
              </button>

              <button
                className="btn-tactical"
                onClick={handleRemovePoint}
                disabled={polygon.length <= 3}
                title="Remove Last Node"
              >
                <Trash2 size={13} color="#ef4444" />
                REMOVE NODE
              </button>
            </div>
          </div>
        </div>

        <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
          <button className="btn-tactical" onClick={onClose}>
            CANCEL
          </button>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {savedSuccess && (
              <span className="mono" style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={14} /> FENCE SAVED TO PIPELINE
              </span>
            )}
            <button
              className="btn-tactical"
              style={{ background: '#0284c7', borderColor: '#38bdf8', color: '#fff', padding: '6px 14px' }}
              onClick={handleSave}
              disabled={saving}
            >
              <Save size={14} />
              {saving ? 'SAVING...' : 'APPLY & PERSIST FENCE'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
