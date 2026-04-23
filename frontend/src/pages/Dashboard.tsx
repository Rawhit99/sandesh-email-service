import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Email as EmailIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Schedule as ScheduleIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService, { Stats } from '../services/api';
import SendNotificationDialog from '../components/SendNotificationDialog';

const initialStats: Stats = {
  total_notifications: 0,
  total_templates: 0,
  notifications_24h: 0,
  success_rate: 0,
  status_counts: {},
  success_count: 0,
  failed_count: 0,
  pending_count: 0,
  recent_notifications: [],
};

/* ── individual KPI tile ─────────────────────────────────────────── */
interface KpiProps {
  label: string;
  value: number;
  sub: string;
  icon: React.ReactNode;
  status: 'neutral' | 'success' | 'error' | 'warning';
  onClick: () => void;
}

function KpiTile({ label, value, sub, icon, status, onClick }: KpiProps) {
  const statusColor: Record<string, string> = {
    neutral: '#0972d3',
    success: '#1d8102',
    error: '#d91515',
    warning: '#b65607',
  };
  const statusBg: Record<string, string> = {
    neutral: '#eff6ff',
    success: '#f2f9f2',
    error: '#fdf0f0',
    warning: '#fef6ee',
  };
  return (
    <Box
      onClick={onClick}
      sx={{
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        p: 2.5,
        cursor: 'pointer',
        transition: 'border-color 0.15s, box-shadow 0.15s',
        '&:hover': {
          borderColor: '#0972d3',
          boxShadow: '0 2px 8px rgba(9,114,211,0.14)',
        },
      }}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {label}
        </Typography>
        <Box sx={{ bgcolor: statusBg[status], borderRadius: 1, p: 0.75 }}>
          {React.cloneElement(icon as React.ReactElement, { sx: { fontSize: 16, color: statusColor[status] } })}
        </Box>
      </Stack>
      <Typography sx={{ fontSize: '2rem', fontWeight: 700, lineHeight: 1, color: 'text.primary', mb: 0.75 }}>
        {value}
      </Typography>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        {sub}
      </Typography>
    </Box>
  );
}

/* ── page ────────────────────────────────────────────────────────── */
const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>(initialStats);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [openSend, setOpenSend] = useState(false);
  const navigate = useNavigate();

  const load = async (background = false) => {
    try {
      background ? setRefreshing(true) : setLoading(true);
      setError(null);
      const data = await apiService.getStats();
      setStats(data);
    } catch {
      setError('Failed to fetch dashboard data. Please try again.');
    } finally {
      background ? setRefreshing(false) : setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const kpis = useMemo(() => [
    { key: 'all',     label: 'Total notifications',  value: stats.total_notifications, sub: 'All statuses',              icon: <EmailIcon />,        status: 'neutral'  as const },
    { key: 'success', label: 'Successful',            value: stats.success_count,        sub: 'Successfully delivered',    icon: <CheckCircleIcon />,  status: 'success'  as const },
    { key: 'failed',  label: 'Failed',                value: stats.failed_count,         sub: 'Requires attention',        icon: <ErrorIcon />,        status: 'error'    as const },
    { key: 'pending', label: 'In progress',           value: stats.pending_count,        sub: 'Pending, queued, running',  icon: <ScheduleIcon />,     status: 'warning'  as const },
  ], [stats]);

  if (loading) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100%', display: 'grid', placeItems: 'center', pt: 8 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100%' }}>
      {/* ── Page header band ─────────────────────────────────────── */}
      <Box sx={{ bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', px: { xs: 2, md: 3 }, pt: 2.5, pb: 2 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.75 }}>
          Console › Dashboard
        </Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4">Dashboard</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              Overview of notifications and delivery health
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexShrink={0}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon sx={{ fontSize: 15 }} />}
              onClick={() => void load(true)}
              disabled={refreshing}
              size="small"
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<SendIcon sx={{ fontSize: 15 }} />}
              onClick={() => setOpenSend(true)}
              size="small"
            >
              Send notification
            </Button>
          </Stack>
        </Stack>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip
            size="small"
            variant="outlined"
            label="System operational"
            color="success"
            sx={{ fontWeight: 600 }}
          />
          <Chip size="small" variant="outlined" label={`${stats.total_templates} templates`} />
          <Chip size="small" variant="outlined" label={`${Math.round(stats.success_rate)}% success rate`} />
          <Chip size="small" variant="outlined" label={`${stats.notifications_24h} in last 24 h`} />
        </Stack>
      </Box>

      {refreshing && <LinearProgress />}

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {/* KPI row */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {kpis.map((kpi) => (
            <Grid item xs={12} sm={6} md={3} key={kpi.key}>
              <KpiTile
                label={kpi.label}
                value={kpi.value}
                sub={kpi.sub}
                icon={kpi.icon}
                status={kpi.status}
                onClick={() => navigate(`/notifications?status=${kpi.key}`)}
              />
            </Grid>
          ))}
        </Grid>

        {/* Overview panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
          {/* panel header */}
          <Box sx={{ px: 2.5, py: 1.75, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Delivery overview</Typography>
            <Typography variant="caption" color="text.secondary">All time</Typography>
          </Box>
          {/* stat rows */}
          <Box sx={{ px: 2.5 }}>
            {[
              { label: 'Total notifications sent',  value: stats.total_notifications },
              { label: 'Successful deliveries',      value: stats.success_count },
              { label: 'Failed deliveries',          value: stats.failed_count },
              { label: 'Pending / in-progress',      value: stats.pending_count },
              { label: 'Active templates',           value: stats.total_templates },
              { label: 'Notifications in last 24 h', value: stats.notifications_24h },
            ].map((row, idx, arr) => (
              <React.Fragment key={row.label}>
                <Box sx={{ py: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">{row.label}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: 'text.primary' }}>{row.value}</Typography>
                </Box>
                {idx < arr.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </Box>
        </Box>
      </Box>

      <SendNotificationDialog
        open={openSend}
        onClose={() => setOpenSend(false)}
        onSuccess={() => {
          setSuccess('Notification queued successfully.');
          void load(true);
        }}
      />
    </Box>
  );
};

export default Dashboard;
