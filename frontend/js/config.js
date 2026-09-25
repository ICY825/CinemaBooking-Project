// Runtime configuration. With docker compose, nginx proxies /api to the backend (same origin).
// If you serve the frontend some other way, point apiBase at the API directly,
// e.g. 'http://localhost:8000/api/v1' (that origin must be listed in CORS_ORIGINS).
window.APP_CONFIG = {
  apiBase: '/api/v1',
  mailhogUrl: 'http://localhost:8025'
};
