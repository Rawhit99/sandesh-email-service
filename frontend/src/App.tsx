import React, { useEffect, useMemo, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, CircularProgress } from '@mui/material';
import { createAppTheme } from './theme';
import { readStoredColorMode } from './theme/colorMode';
import { MainLayout } from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Templates from './pages/Templates';
import Settings from './pages/Settings';
import Notifications from './pages/Notifications';
import Login from './pages/Login';
import Register from './pages/Register';
import ApiKeys from './pages/ApiKeys';
import Subscribers from './pages/Subscribers';
import Integrations from './pages/Integrations';
import Organizations from './pages/Organizations';
import { clearSession, hasActiveSession, setupSessionIdleTimer } from './services/session';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [colorMode, setColorMode] = useState<'light' | 'dark'>(() => readStoredColorMode());

  useEffect(() => {
    setIsAuthenticated(hasActiveSession());
    setLoading(false);
  }, []);

  useEffect(() => setupSessionIdleTimer(() => {
    clearSession();
    setIsAuthenticated(false);
    if (window.location.pathname !== '/login') {
      window.location.assign('/login');
    }
  }), []);

  useEffect(() => {
    const handler = (e: Event) => {
      const ce = e as CustomEvent<'light' | 'dark'>;
      if (ce.detail === 'light' || ce.detail === 'dark') {
        setColorMode(ce.detail);
      }
    };
    window.addEventListener('sandesh-theme-change', handler as EventListener);
    return () => window.removeEventListener('sandesh-theme-change', handler as EventListener);
  }, []);

  const theme = useMemo(() => createAppTheme(colorMode), [colorMode]);

  const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
    if (loading) {
      return (
        <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
          <CircularProgress />
        </Box>
      );
    }
    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/*"
            element={
              <PrivateRoute>
                <MainLayout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/notifications" element={<Notifications />} />
                    <Route path="/templates" element={<Templates />} />
                    <Route path="/subscribers" element={<Subscribers />} />
                    <Route path="/integrations" element={<Integrations />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/organizations" element={<Organizations />} />
                    <Route path="/organization" element={<Navigate to="/organizations" replace />} />
                    <Route path="/api-keys" element={<ApiKeys />} />
                  </Routes>
                </MainLayout>
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
