import React, { useMemo, useState, useEffect } from 'react';
import {
  Box,
  CardActionArea,
  Chip,
  Divider,
  Stack,
  Typography,
} from '@mui/material';
import {
  Business as BusinessIcon,
  ChevronRight as ChevronRightIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  VpnKey as VpnKeyIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { persistColorMode, readStoredColorMode } from '../theme/colorMode';

interface SettingRow {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  iconBg: string;
  iconColor: string;
  onClick: () => void;
  disabled?: boolean;
}

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'light' | 'dark'>(() => readStoredColorMode());

  useEffect(() => {
    const handler = (e: Event) => {
      const ce = e as CustomEvent<'light' | 'dark'>;
      if (ce.detail === 'light' || ce.detail === 'dark') setMode(ce.detail);
    };
    window.addEventListener('sandesh-theme-change', handler as EventListener);
    return () => window.removeEventListener('sandesh-theme-change', handler as EventListener);
  }, []);

  const toggleMode = () => {
    const next = mode === 'light' ? 'dark' : 'light';
    setMode(next);
    persistColorMode(next);
  };

  const rows: SettingRow[] = useMemo(() => [
    {
      title: 'API Keys',
      subtitle: 'Create and revoke keys for programmatic access to Sandesh.',
      icon: <VpnKeyIcon sx={{ fontSize: 20 }} />,
      iconBg: '#eff6ff',
      iconColor: '#0972d3',
      onClick: () => navigate('/api-keys'),
    },
    {
      title: mode === 'light' ? 'Dark mode' : 'Light mode',
      subtitle: `Switch to ${mode === 'light' ? 'dark' : 'light'} theme. Applies on this browser only.`,
      icon: mode === 'light' ? <DarkModeIcon sx={{ fontSize: 20 }} /> : <LightModeIcon sx={{ fontSize: 20 }} />,
      iconBg: 'background.default',
      iconColor: '#545b64',
      onClick: toggleMode,
    },
    {
      title: 'Organizations',
      subtitle: 'Platform admins: create customer orgs and switch context in the top bar.',
      icon: <BusinessIcon sx={{ fontSize: 20 }} />,
      iconBg: '#eff6ff',
      iconColor: '#0972d3',
      onClick: () => navigate('/organizations'),
    },
  ], [mode, navigate]);

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100%' }}>
      {/* ── Page header band ─────────────────────────────────────── */}
      <Box sx={{ bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', px: { xs: 2, md: 3 }, pt: 2.5, pb: 2 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.75 }}>
          Console › Settings
        </Typography>
        <Typography variant="h4">Settings</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
          Manage preferences and account settings. Channel integrations live under Integrations.
        </Typography>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }}>
          <Chip size="small" variant="outlined" label={`Theme: ${mode}`} />
          <Chip size="small" variant="outlined" label="Account preferences" />
        </Stack>
      </Box>

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
          {rows.map((row, idx) => (
            <React.Fragment key={row.title}>
              <CardActionArea onClick={row.onClick} disabled={row.disabled}>
                <Box sx={{ px: 2.5, py: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                  {/* Icon tile */}
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: 1,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: row.iconBg,
                      color: row.iconColor,
                      border: '1px solid',
                      borderColor: 'divider',
                      flexShrink: 0,
                    }}
                  >
                    {row.icon}
                  </Box>

                  {/* Text */}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="body1" sx={{ fontWeight: 600, color: 'text.primary', lineHeight: 1.3 }}>
                      {row.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25, display: 'block' }}>
                      {row.subtitle}
                    </Typography>
                  </Box>

                  {/* Chevron */}
                  <ChevronRightIcon sx={{ fontSize: 18, color: 'text.secondary', opacity: 0.7, flexShrink: 0 }} />
                </Box>
              </CardActionArea>
              {idx < rows.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export default Settings;
