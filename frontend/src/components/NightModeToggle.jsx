import React from 'react';
import { Moon, Sun } from 'lucide-react';

export function NightModeToggle({ nightMode, onToggle, cameraId }) {
  return (
    <button
      className={`btn-tactical ${nightMode ? 'active-night' : ''}`}
      onClick={() => onToggle(cameraId, !nightMode)}
      title="Toggle CLAHE Low-Light Night Enhancement"
    >
      {nightMode ? <Moon size={13} color="#38bdf8" /> : <Sun size={13} />}
      <span>{nightMode ? 'NIGHT CLAHE: ON' : 'NIGHT CLAHE: OFF'}</span>
    </button>
  );
}
