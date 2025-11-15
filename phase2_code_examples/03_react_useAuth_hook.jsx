/**
 * React Auth Hook mit Context
 * Phase 2: Cookie-basierte Authentifizierung
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

const AuthContext = createContext(null);

/**
 * Auth Provider Component
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Bei App-Start: Auth-Status prüfen
  useEffect(() => {
    checkAuthStatus();
  }, []);

  /**
   * Prüft den aktuellen Authentifizierungs-Status
   * Nutzt /api/auth/me Endpoint (Cookie wird automatisch gesendet)
   */
  async function checkAuthStatus() {
    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        credentials: 'include', // ✅ Cookie wird automatisch gesendet
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }

  /**
   * Login-Funktion
   * @param {string} email - Benutzer-Email
   * @param {string} code - Login-Code
   * @returns {Promise<boolean>} - true bei Erfolg
   */
  async function login(email, code) {
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // ✅ Cookie wird automatisch empfangen
        body: JSON.stringify({ email, code }),
      });

      if (response.ok) {
        // Nach erfolgreichem Login: Auth-Status neu laden
        await checkAuthStatus();
        return true;
      } else {
        const error = await response.json();
        console.error('Login failed:', error);
        return false;
      }
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  }

  /**
   * Logout-Funktion
   * Ruft Backend-Endpoint auf zum Cookie löschen
   */
  async function logout() {
    try {
      await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include', // ✅ Cookie wird gesendet
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  }

  /**
   * Code-Anforderung für Magic-Link Login
   * @param {string} email - Benutzer-Email
   * @returns {Promise<boolean>} - true bei Erfolg
   */
  async function requestCode(email) {
    try {
      const response = await fetch(`${API_URL}/api/auth/request-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email }),
      });

      return response.ok;
    } catch (error) {
      console.error('Request code error:', error);
      return false;
    }
  }

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    requestCode,
    checkAuthStatus,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook zum Zugriff auf Auth-Context
 * @returns {Object} Auth context value
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

/**
 * VERWENDUNG:
 *
 * // In App.jsx:
 * import { AuthProvider } from './hooks/useAuth';
 *
 * function App() {
 *   return (
 *     <AuthProvider>
 *       <Router>
 *         <Routes />
 *       </Router>
 *     </AuthProvider>
 *   );
 * }
 *
 * // In einer Komponente:
 * import { useAuth } from './hooks/useAuth';
 *
 * function LoginPage() {
 *   const { login, requestCode } = useAuth();
 *
 *   const handleLogin = async (email, code) => {
 *     const success = await login(email, code);
 *     if (success) {
 *       navigate('/dashboard');
 *     }
 *   };
 * }
 *
 * function Dashboard() {
 *   const { user, logout } = useAuth();
 *
 *   return (
 *     <div>
 *       <h1>Welcome, {user.email}</h1>
 *       <button onClick={logout}>Logout</button>
 *     </div>
 *   );
 * }
 */
