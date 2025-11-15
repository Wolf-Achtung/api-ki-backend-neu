/**
 * API Client mit Fetch API
 * Phase 2: Cookie-basierte Authentifizierung
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

/**
 * Generic API request function
 * @param {string} endpoint - API endpoint (e.g., '/api/auth/me')
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>}
 */
export async function apiRequest(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // ✅ NEU: Cookies automatisch senden
    ...options,
  };

  const response = await fetch(url, defaultOptions);

  // Optional: Auto-Logout bei 401
  if (response.status === 401) {
    // User ist nicht authentifiziert - optional zum Login weiterleiten
    // window.location.href = '/login';
  }

  return response;
}

/**
 * GET request
 */
export async function get(endpoint) {
  const response = await apiRequest(endpoint, { method: 'GET' });
  return response.json();
}

/**
 * POST request
 */
export async function post(endpoint, data) {
  const response = await apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return response.json();
}

/**
 * DELETE request
 */
export async function del(endpoint) {
  const response = await apiRequest(endpoint, { method: 'DELETE' });
  return response.json();
}

// Verwendung:
// import { get, post } from './apiClient';
// const userData = await get('/api/auth/me');
// const result = await post('/api/briefings/submit', briefingData);
