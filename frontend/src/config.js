/**
 * Global API and WebSocket Endpoint Configuration.
 * Automatically adapts between local development, Vercel deployments, and Render full-stack hosting.
 */

const IS_VERCEL = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');
const DEFAULT_RENDER_BACKEND = 'https://sentinel-grid-backend.onrender.com';

export const API_BASE_URL = import.meta.env.VITE_API_URL || (IS_VERCEL ? DEFAULT_RENDER_BACKEND : '');
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || (IS_VERCEL ? DEFAULT_RENDER_BACKEND : '');

/**
 * Returns absolute or relative API URL based on environment configuration.
 * @param {string} path - e.g. '/api/cameras' or 'api/cameras'
 */
export function getApiUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  if (API_BASE_URL) {
    const base = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
    return `${base}${cleanPath}`;
  }
  return cleanPath;
}

/**
 * Returns absolute or relative WebSocket URL.
 */
export function getWsUrl() {
  if (WS_BASE_URL) {
    let wsBase = WS_BASE_URL;
    if (wsBase.startsWith('http://')) {
      wsBase = wsBase.replace('http://', 'ws://');
    } else if (wsBase.startsWith('https://')) {
      wsBase = wsBase.replace('https://', 'wss://');
    } else if (!wsBase.startsWith('ws://') && !wsBase.startsWith('wss://')) {
      wsBase = `wss://${wsBase}`;
    }

    wsBase = wsBase.endsWith('/') ? wsBase.slice(0, -1) : wsBase;
    return wsBase.endsWith('/ws/live') ? wsBase : `${wsBase}/ws/live`;
  }

  // Fallback to current browser host
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/ws/live`;
}
