/**
 * API Client mit Axios
 * Phase 2: Cookie-basierte Authentifizierung
 */

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

// Axios-Instanz erstellen
const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true, // ✅ NEU: Cookies automatisch senden (entspricht credentials: 'include')
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response Interceptor (optional): Auto-Logout bei 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // User ist nicht authentifiziert - optional zum Login weiterleiten
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// Verwendung:
// import apiClient from './apiClient';
// const { data } = await apiClient.get('/api/auth/me');
// const { data } = await apiClient.post('/api/briefings/submit', briefingData);
