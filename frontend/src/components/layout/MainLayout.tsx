import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Typography,
  useTheme,
  useMediaQuery,
  CssBaseline,
  Avatar,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  CircularProgress,
  InputBase,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Email as EmailIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  VpnKey as VpnKeyIcon,
  Logout as LogoutIcon,
  Group as GroupIcon,
  Hub as HubIcon,
  Business as BusinessIcon,
  Circle as CircleIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import apiService, { AuthUser, PlatformOrganization } from '../../services/api';
import { clearSession } from '../../services/session';

const drawerWidth = 272;
const brandIconUrl = `${process.env.PUBLIC_URL}/sandesh-icon.png`;

interface User {
  id: number;
  username: string;
  organization_id?: number | null;
  organization_name?: string | null;
  organization_role?: string | null;
  is_platform_admin?: boolean;
  is_active: boolean;
  created_at: string;
}

interface MainLayoutProps {
  children: React.ReactNode;
}

function readUserFromStorage(): User | null {
  if (typeof localStorage === 'undefined') {
    return null;
  }
  const raw = localStorage.getItem('user');
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<User | null>(() => readUserFromStorage());
  const [platformOrgs, setPlatformOrgs] = useState<PlatformOrganization[]>([]);
  const [platformOrgsLoadDone, setPlatformOrgsLoadDone] = useState(false);
  const [authMeResolved, setAuthMeResolved] = useState(false);
  const [selectedOrgId, setSelectedOrgId] = useState<string>(() =>
    typeof localStorage !== 'undefined' ? localStorage.getItem('sandesh-org-id') || '' : '',
  );
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const loadUserFromStorage = () => {
      setUser(readUserFromStorage());
    };
    loadUserFromStorage();
    window.addEventListener('sandesh-user-update', loadUserFromStorage);
    return () => window.removeEventListener('sandesh-user-update', loadUserFromStorage);
  }, []);

  /** Refresh flags (e.g. is_platform_admin from PLATFORM_ADMIN_USERNAMES) before tenant routes run. */
  useEffect(() => {
    const token = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
      setAuthMeResolved(true);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const fresh: AuthUser = await apiService.getAuthMe();
        if (cancelled) {
          return;
        }
        const prev = readUserFromStorage();
        const merged: User = {
          id: fresh.id,
          username: fresh.username,
          organization_id: fresh.organization_id ?? prev?.organization_id,
          organization_name: fresh.organization_name ?? prev?.organization_name ?? null,
          organization_role: fresh.organization_role ?? prev?.organization_role ?? null,
          is_platform_admin: fresh.is_platform_admin,
          is_active: fresh.is_active,
          created_at: fresh.created_at,
        };
        localStorage.setItem('user', JSON.stringify(merged));
        setUser(merged);
        window.dispatchEvent(new Event('sandesh-user-update'));
      } catch {
        /* keep stored user */
      } finally {
        if (!cancelled) {
          setAuthMeResolved(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshPlatformOrgs = useCallback(async () => {
    if (!user) {
      return;
    }
    if (!user.is_platform_admin) {
      setPlatformOrgs([]);
      setPlatformOrgsLoadDone(true);
      return;
    }
    setPlatformOrgsLoadDone(false);
    try {
      const list = await apiService.listPlatformOrganizations();
      setPlatformOrgs(list);
      const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('sandesh-org-id') : null;
      const valid = stored && list.some((o) => String(o.id) === stored);
      if (valid && stored) {
        setSelectedOrgId(stored);
      } else if (list.length > 0) {
        const first = String(list[0].id);
        localStorage.setItem('sandesh-org-id', first);
        setSelectedOrgId(first);
      } else {
        localStorage.removeItem('sandesh-org-id');
        setSelectedOrgId('');
      }
    } catch {
      setPlatformOrgs([]);
    } finally {
      setPlatformOrgsLoadDone(true);
    }
  }, [user]);

  useEffect(() => {
    void refreshPlatformOrgs();
  }, [refreshPlatformOrgs]);

  useEffect(() => {
    const onRefresh = () => void refreshPlatformOrgs();
    window.addEventListener('sandesh-platform-orgs-refresh', onRefresh);
    return () => window.removeEventListener('sandesh-platform-orgs-refresh', onRefresh);
  }, [refreshPlatformOrgs]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = () => {
    clearSession();
    setUser(null);
    setSelectedOrgId('');
    setPlatformOrgs([]);
    navigate('/login');
  };

  const menuItems = useMemo(() => {
    const base: {
      text: string;
      icon: React.ReactNode;
      path: string;
      description: string;
    }[] = [
    { 
      text: 'Dashboard', 
      icon: <DashboardIcon />, 
      path: '/',
      description: 'Overview and analytics'
    },
    { 
      text: 'Notifications', 
      icon: <NotificationsIcon />, 
      path: '/notifications',
      description: 'Email notifications'
    },
    { 
      text: 'Templates', 
      icon: <EmailIcon />, 
      path: '/templates',
      description: 'Email templates'
    },
    {
      text: 'Subscribers',
      icon: <GroupIcon />,
      path: '/subscribers',
      description: 'Delivery targets (Novu-style)',
    },
    {
      text: 'Integrations',
      icon: <HubIcon />,
      path: '/integrations',
      description: 'Slack, Teams, FCM, SNS, queue',
    },
    { 
      text: 'API Keys', 
      icon: <VpnKeyIcon />, 
      path: '/api-keys',
      description: 'Manage API access'
    },
    { 
      text: 'Settings', 
      icon: <SettingsIcon />, 
      path: '/settings',
      description: 'System configuration'
    },
  ];
    if (user?.is_platform_admin) {
      base.splice(base.length - 1, 0, {
        text: 'Organizations',
        icon: <BusinessIcon />,
        path: '/organizations',
        description: 'Customer orgs and tenant accounts',
      });
    }
    return base;
  }, [user?.is_platform_admin]);

  const selectedOrgLabel = useMemo(() => {
    if (!user?.is_platform_admin || !selectedOrgId) {
      return null;
    }
    const o = platformOrgs.find((x) => String(x.id) === selectedOrgId);
    return o?.name ?? null;
  }, [user?.is_platform_admin, selectedOrgId, platformOrgs]);

  const tenantContextReady = useMemo(() => {
    if (!authMeResolved) {
      return false;
    }
    if (!user) {
      return false;
    }
    if (!user.is_platform_admin) {
      return true;
    }
    if (!platformOrgsLoadDone) {
      return false;
    }
    if (platformOrgs.length === 0) {
      return true;
    }
    return Boolean(selectedOrgId && platformOrgs.some((o) => String(o.id) === selectedOrgId));
  }, [authMeResolved, user, platformOrgsLoadDone, platformOrgs, selectedOrgId]);

  const onOrgSelect = (orgId: string) => {
    setSelectedOrgId(orgId);
    if (orgId) {
      localStorage.setItem('sandesh-org-id', orgId);
    } else {
      localStorage.removeItem('sandesh-org-id');
    }
    window.dispatchEvent(new Event('sandesh-org-change'));
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider', backgroundColor: 'background.paper' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
          <Box
            component="img"
            src={brandIconUrl}
            alt="Sandesh"
            sx={{ width: 44, height: 44, objectFit: 'contain', flexShrink: 0, mr: 1.5 }}
          />
          <Box>
            <Typography variant="body1" sx={{ fontWeight: 700, color: 'text.primary' }}>
              Sandesh
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Notification Platform
            </Typography>
          </Box>
        </Box>
        <Chip label="Console" size="small" variant="outlined" sx={{ height: 20, fontWeight: 600 }} />
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, p: 1.5, backgroundColor: 'background.paper' }}>
        <List sx={{ px: 0 }}>
          {menuItems.map((item) => (
            <ListItem
              key={item.text}
              onClick={() => {
                navigate(item.path);
                if (isMobile) {
                  setMobileOpen(false);
                }
              }}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 1.5,
                mb: 0.25,
                py: 0.5,
                cursor: 'pointer',
                '&.Mui-selected': {
                  backgroundColor: 'action.selected',
                  borderLeft: '2px solid #0972d3',
                  color: '#0972d3',
                  '&:hover': {
                    backgroundColor: 'action.selected',
                  },
                  '& .MuiListItemIcon-root': {
                    color: '#0972d3',
                  },
                  '& .MuiListItemText-primary': {
                    fontWeight: 600,
                  },
                },
                '&:hover': { backgroundColor: 'action.hover' },
              }}
            >
              <ListItemIcon sx={{ minWidth: 32, color: 'text.secondary' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.8125rem',
                  fontWeight: location.pathname === item.path ? 600 : 500,
                  color: location.pathname === item.path ? 'primary.main' : 'text.primary',
                }}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Footer */}
      <Box sx={{ p: 1.5, borderTop: '1px solid', borderColor: 'divider', backgroundColor: 'background.paper' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
          <Avatar sx={{ width: 28, height: 28, mr: 1.5, bgcolor: '#0972d3', fontSize: 12 }}>
            {user?.username ? user.username.charAt(0).toUpperCase() : 'U'}
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
              {user?.organization_name || 'User Account'}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              {user?.username || 'user@company.com'}
            </Typography>
          </Box>
        </Box>
        <IconButton
          onClick={handleLogout}
          sx={{
            width: '100%',
            justifyContent: 'flex-start',
            color: 'text.secondary',
            '&:hover': {
              backgroundColor: 'action.hover',
              color: 'text.primary',
            },
          }}
        >
          <LogoutIcon sx={{ mr: 2, fontSize: 20 }} />
          <Typography variant="body2" sx={{ fontSize: '0.8125rem' }}>Logout</Typography>
        </IconButton>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          backgroundColor: 'background.paper',
          color: 'text.primary',
          boxShadow: 'none',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Box
          sx={{
            minHeight: 36,
            px: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 2,
            bgcolor: '#0f1b2a',
            color: '#d5dbdb',
            borderBottom: '1px solid #2a3443',
          }}
        >
          <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
            <CircleIcon sx={{ fontSize: 10, color: '#1d8102' }} />
            Sandesh Console
            {selectedOrgLabel ? ` / ${selectedOrgLabel}` : ''}
          </Typography>
          <Box
            sx={{
              flex: 1,
              maxWidth: 520,
              height: 22,
              border: '1px solid #314357',
              borderRadius: 0.75,
              px: 1.25,
              display: { xs: 'none', md: 'flex' },
              alignItems: 'center',
              bgcolor: '#111c2c',
            }}
          >
            <InputBase
              placeholder="Search"
              sx={{ fontSize: '0.75rem', color: '#d5dbdb', width: '100%' }}
              inputProps={{ 'aria-label': 'search' }}
            />
          </Box>
          <Typography variant="caption" sx={{ color: '#9ba7b6' }}>
            {user?.username ?? 'anonymous'}
          </Typography>
        </Box>
        <Toolbar sx={{ minHeight: '58px !important', px: 2 }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ flex: 1 }}>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Sandesh / Console
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', textTransform: 'none', mt: 0.25 }}>
              {menuItems.find((item) => item.path === location.pathname)?.text ||
                (location.pathname === '/organizations' ? 'Organizations' : 'Dashboard')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            {user?.is_platform_admin && platformOrgs.length > 0 && (
              <FormControl size="small" sx={{ minWidth: 200 }}>
                <InputLabel id="sandesh-org-select-label">Organization</InputLabel>
                <Select
                  labelId="sandesh-org-select-label"
                  label="Organization"
                  value={selectedOrgId}
                  onChange={(e) => onOrgSelect(String(e.target.value))}
                >
                  {platformOrgs.map((o) => (
                    <MenuItem key={o.id} value={String(o.id)}>
                      {o.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            {user?.is_platform_admin && platformOrgs.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 280 }}>
                No organizations yet —{' '}
                <Box component="span" sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={() => navigate('/organizations')}>
                  create one
                </Box>
              </Typography>
            )}
            <Chip label={user?.is_platform_admin ? 'Platform Admin' : 'Workspace'} size="small" variant="outlined" sx={{ height: 22, fontWeight: 600 }} />
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              backgroundColor: 'background.paper',
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: 'background.default',
          minHeight: '100vh',
        }}
      >
        <Box sx={{ height: 94 }} />
        <Box sx={{ p: 0 }}>
          {tenantContextReady ? (
            // key forces all page components to remount (and re-fetch) when the
            // selected organisation changes so they never show stale data.
            <React.Fragment key={selectedOrgId}>
              {children}
            </React.Fragment>
          ) : (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                minHeight: '40vh',
                px: 3,
              }}
            >
              <CircularProgress />
              <Typography variant="body2" color="text.secondary" textAlign="center">
                {!authMeResolved
                  ? 'Confirming your account…'
                  : user?.is_platform_admin
                    ? 'Loading organizations and tenant context…'
                    : 'Loading your session…'}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};
