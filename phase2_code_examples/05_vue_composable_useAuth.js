/**
 * Vue 3 Composable für Authentifizierung
 * Phase 2: Cookie-basierte Authentifizierung
 */

import { ref, computed } from 'vue';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// Shared state (reactive)
const user = ref(null);
const isLoading = ref(false);

/**
 * Auth Composable
 * @returns {Object} Auth functions and state
 */
export function useAuth() {
  // Computed properties
  const isAuthenticated = computed(() => !!user.value);

  /**
   * Prüft den aktuellen Authentifizierungs-Status
   */
  async function checkAuthStatus() {
    isLoading.value = true;
    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        credentials: 'include', // ✅ Cookie wird automatisch gesendet
      });

      if (response.ok) {
        user.value = await response.json();
      } else {
        user.value = null;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      user.value = null;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Login-Funktion
   * @param {string} email - Benutzer-Email
   * @param {string} code - Login-Code
   * @returns {Promise<boolean>} - true bei Erfolg
   */
  async function login(email, code) {
    isLoading.value = true;
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
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Logout-Funktion
   */
  async function logout() {
    isLoading.value = true;
    try {
      await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      user.value = null;
      isLoading.value = false;
    }
  }

  /**
   * Code-Anforderung für Magic-Link Login
   * @param {string} email - Benutzer-Email
   * @returns {Promise<boolean>} - true bei Erfolg
   */
  async function requestCode(email) {
    isLoading.value = true;
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
    } finally {
      isLoading.value = false;
    }
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    requestCode,
    checkAuthStatus,
  };
}

/**
 * VERWENDUNG in Komponenten:
 *
 * <template>
 *   <div v-if="isLoading">Loading...</div>
 *   <div v-else-if="isAuthenticated">
 *     <h1>Welcome, {{ user.email }}</h1>
 *     <button @click="logout">Logout</button>
 *   </div>
 *   <div v-else>
 *     <LoginForm @submit="handleLogin" />
 *   </div>
 * </template>
 *
 * <script setup>
 * import { onMounted } from 'vue';
 * import { useAuth } from './composables/useAuth';
 *
 * const { user, isAuthenticated, isLoading, login, logout, checkAuthStatus } = useAuth();
 *
 * onMounted(() => {
 *   checkAuthStatus();
 * });
 *
 * async function handleLogin(email, code) {
 *   const success = await login(email, code);
 *   if (success) {
 *     router.push('/dashboard');
 *   }
 * }
 * </script>
 */

/**
 * VERWENDUNG mit Vue Router Navigation Guard:
 *
 * // router/index.js
 * import { useAuth } from '@/composables/useAuth';
 *
 * router.beforeEach(async (to, from, next) => {
 *   const { isAuthenticated, checkAuthStatus } = useAuth();
 *
 *   if (to.meta.requiresAuth) {
 *     await checkAuthStatus();
 *
 *     if (isAuthenticated.value) {
 *       next();
 *     } else {
 *       next('/login');
 *     }
 *   } else {
 *     next();
 *   }
 * });
 *
 * // Route-Definition:
 * {
 *   path: '/dashboard',
 *   component: Dashboard,
 *   meta: { requiresAuth: true }
 * }
 */
