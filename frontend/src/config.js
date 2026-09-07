/**
 * Global API and WebSocket Endpoint Configuration.
 * Automatically adapts between local development and cloud production (Vercel + Render/Railway).
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || '';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || '';

/**
 * Returns absolute or relative API URL based on environment configuration.
 * @param {string} path - e.g. '/api/cameras' or 'api/cameras'
 */
export function getApiUrl(path) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
}

/**
 * Returns absolute or relative WebSocket URL.
 */
export function getWsUrl() {
  if (WS_BASE_URL) {
    if (WS_BASE_URL.startsWith('http://')) {
      return WS_BASE_URL.replace('http://', 'ws://') + (WS_BASE_URL.endsWith('/ws/live') ? '' : '/ws/live');
    }
    if (WS_BASE_URL.startsWith('https://')) {
      return WS_BASE_URL.replace('https://', 'wss://') + (WS_BASE_URL.endsWith('/ws/live') ? '' : '/ws/live');
    }
    return WS_BASE_URL.endsWith('/ws/live') ? WS_BASE_URL : `${WS_BASE_URL}/ws/live`;
  }

  // Fallback to current host if VITE_WS_URL is not set
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/ws/live`;
}
