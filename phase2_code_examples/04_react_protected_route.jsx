/**
 * Protected Route Component
 * Phase 2: Cookie-basierte Authentifizierung
 * React Router v6
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from './useAuth'; // Ihr Auth Hook

/**
 * Protected Route Wrapper
 * Leitet zur Login-Seite weiter, wenn User nicht authentifiziert ist
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  // Während Auth-Check läuft: Spinner zeigen
  if (isLoading) {
    return (
      <div className="loading-spinner">
        <p>Loading...</p>
      </div>
    );
  }

  // Nicht authentifiziert: Zur Login-Seite weiterleiten
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Authentifiziert: Komponente rendern
  return children;
}

/**
 * VERWENDUNG:
 *
 * // In App.jsx oder Router-Konfiguration:
 * import { BrowserRouter, Routes, Route } from 'react-router-dom';
 * import { ProtectedRoute } from './components/ProtectedRoute';
 *
 * function App() {
 *   return (
 *     <BrowserRouter>
 *       <Routes>
 *         <Route path="/login" element={<LoginPage />} />
 *
 *         <Route
 *           path="/dashboard"
 *           element={
 *             <ProtectedRoute>
 *               <Dashboard />
 *             </ProtectedRoute>
 *           }
 *         />
 *
 *         <Route
 *           path="/briefings"
 *           element={
 *             <ProtectedRoute>
 *               <BriefingsPage />
 *             </ProtectedRoute>
 *           }
 *         />
 *       </Routes>
 *     </BrowserRouter>
 *   );
 * }
 */

/**
 * ALTERNATIVE: Mit redirect state
 * Speichert die ursprünglich angeforderte URL für Redirect nach Login
 */
export function ProtectedRouteWithRedirect({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div className="loading-spinner">Loading...</div>;
  }

  if (!isAuthenticated) {
    // Speichert die aktuelle URL für Redirect nach Login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

/**
 * Login-Komponente mit Redirect-Unterstützung:
 */
/*
function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogin = async (email, code) => {
    const success = await login(email, code);
    if (success) {
      // Redirect zur ursprünglich angeforderten Seite oder Dashboard
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  };

  // ... rest of component
}
*/
