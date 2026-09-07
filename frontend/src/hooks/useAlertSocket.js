import { useState, useEffect, useRef, useCallback } from 'react';
import { getApiUrl, getWsUrl } from '../config';

export function useAlertSocket() {
  const [connected, setConnected] = useState(false);
  const [frames, setFrames] = useState({}); // { [camera_id]: { image, fps, active_tracks } }
  const [alerts, setAlerts] = useState([]);
  const [threatLevel, setThreatLevel] = useState('LOW');
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Load initial alerts from REST API on mount
  useEffect(() => {
    fetch(getApiUrl('/api/alerts?limit=30'))
      .then((res) => (res.ok ? res.json() : []))
      .then((initialAlerts) => {
        if (Array.isArray(initialAlerts)) {
          setAlerts(initialAlerts);
        }
      })
      .catch((err) => console.warn('[useAlertSocket] Error fetching initial alerts:', err));
  }, []);

  const connect = useCallback(() => {
    const wsUrl = getWsUrl();
    console.log('[WebSocket] Connecting to:', wsUrl);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WebSocket] Connected successfully to:', wsUrl);
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          if (msg.type === 'frame') {
            setFrames((prev) => ({
              ...prev,
              [msg.camera_id]: {
                image: msg.image,
                fps: msg.fps,
                active_tracks: msg.active_tracks,
                timestamp: msg.timestamp
              }
            }));
          } else if (msg.type === 'alert') {
            const newAlert = msg.data;
            setAlerts((prev) => {
              const filtered = prev.filter((a) => a.alert_id !== newAlert.alert_id);
              return [newAlert, ...filtered].slice(0, 100);
            });

            if (newAlert.risk_score >= 80) {
              setThreatLevel('CRITICAL');
            } else if (newAlert.risk_score >= 60) {
              setThreatLevel((curr) => (curr === 'CRITICAL' ? 'CRITICAL' : 'ELEVATED'));
            }
          }
        } catch (err) {
          console.error('[WebSocket] Message parsing error:', err);
        }
      };

      ws.onclose = (evt) => {
        console.log(`[WebSocket] Disconnected (code: ${evt.code}). Reconnecting in 2.5s...`);
        setConnected(false);
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 2500);
      };

      ws.onerror = (err) => {
        console.warn('[WebSocket] Connection error:', err);
        ws.close();
      };
    } catch (e) {
      console.error('[WebSocket] Failed to instantiate WebSocket:', e);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    connect();

    // Heartbeat ping every 10 seconds
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'ping' }));
      }
    }, 10000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const acknowledgeAlert = async (alertId) => {
    try {
      await fetch(getApiUrl(`/api/alerts/${alertId}/acknowledge`), { method: 'POST' });
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, acknowledged: true } : a))
      );
    } catch (e) {
      console.error('Failed to acknowledge alert:', e);
    }
  };

  const clearAlerts = () => {
    setAlerts([]);
    setThreatLevel('LOW');
  };

  return {
    connected,
    frames,
    alerts,
    threatLevel,
    acknowledgeAlert,
    clearAlerts
  };
}
