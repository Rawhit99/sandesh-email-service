import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Snackbar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Email as EmailIcon,
  Error as ErrorIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterListIcon,
  MarkEmailRead as MarkEmailReadIcon,
  MarkEmailUnread as MarkEmailUnreadIcon,
  Pending as PendingIcon,
  Refresh as RefreshIcon,
  Replay as ReplayIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useSearchParams } from 'react-router-dom';
import apiService, { Notification } from '../services/api';

const Notifications: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [page, setPage] = useState(1);
  const rowsPerPage = 10;
  const [activeTab, setActiveTab] = useState(0);
  const [retryLoading, setRetryLoading] = useState<number | null>(null);
  const [resendLoading, setResendLoading] = useState<number | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success',
  });

  const fetchNotifications = useCallback(async (background = false) => {
    try {
      background ? setRefreshing(true) : setLoading(true);
      setError(null);
      const status = searchParams.get('status') || 'all';
      const data = await apiService.getNotifications({ status });
      setNotifications(data || []);
    } catch {
      setError('Failed to fetch notifications');
    } finally {
      background ? setRefreshing(false) : setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => { void fetchNotifications(false); }, [fetchNotifications]);
  useEffect(() => {
    const id = window.setInterval(() => void fetchNotifications(true), 15000);
    return () => window.clearInterval(id);
  }, [fetchNotifications]);
  useEffect(() => {
    const status = searchParams.get('status') || 'all';
    const map: Record<string, number> = { all: 0, success: 1, failed: 2, pending: 3 };
    setActiveTab(map[status] ?? 0);
  }, [searchParams]);

  const handleRetry = async (notificationId: number) => {
    try {
      setRetryLoading(notificationId);
      await apiService.retryNotification(notificationId);
      setSnackbar({ open: true, message: 'Retry initiated', severity: 'success' });
      setTimeout(() => { void fetchNotifications(); }, 1000);
    } catch {
      setSnackbar({ open: true, message: 'Failed to retry', severity: 'error' });
    } finally { setRetryLoading(null); }
  };

  const handleRetryMultiple = async (ids: number[]) => {
    try {
      await Promise.all(ids.map(id => apiService.retryNotification(id)));
      setSuccess(`Retried ${ids.length} notifications`);
      setTimeout(() => { void fetchNotifications(); }, 1000);
    } catch { setError('Failed to retry some notifications'); }
  };

  const handleResend = async (notificationId: number) => {
    try {
      setResendLoading(notificationId);
      await apiService.resendNotification(notificationId);
      setSnackbar({ open: true, message: 'Resend initiated', severity: 'success' });
      setTimeout(() => { void fetchNotifications(); }, 1000);
    } catch {
      setSnackbar({ open: true, message: 'Failed to resend', severity: 'error' });
    } finally { setResendLoading(null); }
  };

  const handleMarkSeen = async (id: number, markAsRead: boolean) => {
    try {
      if (markAsRead) await apiService.markNotificationSeen(id);
      else await apiService.markNotificationUnseen(id);
      await fetchNotifications();
    } catch { /* ignore */ }
  };

  const getStatusChip = (status: string) => {
    if (status === 'success') return <Chip icon={<CheckCircleIcon />} label="Success" color="success" size="small" />;
    if (status === 'failed')  return <Chip icon={<ErrorIcon />}        label="Failed"  color="error"   size="small" />;
    if (['pending','queued','running'].includes(status)) return <Chip icon={<PendingIcon />} label={status} color="warning" size="small" />;
    return <Chip label={status} size="small" variant="outlined" />;
  };

  const toggleRow = (id: number) => {
    const next = new Set(expandedRows);
    next.has(id) ? next.delete(id) : next.add(id);
    setExpandedRows(next);
  };

  // Reset to page 1 whenever search term changes
  useEffect(() => { setPage(1); }, [searchTerm]);

  const filteredNotifications = notifications.filter(n =>
    n.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    n.template_id.toLowerCase().includes(searchTerm.toLowerCase()),
  );
  const computedTotalPages     = Math.max(1, Math.ceil(filteredNotifications.length / rowsPerPage));
  const paginatedNotifications = filteredNotifications.slice((page - 1) * rowsPerPage, page * rowsPerPage);
  const failedNotifications   = filteredNotifications.filter(n => n.status === 'failed');
  const successNotifications  = filteredNotifications.filter(n => n.status === 'success');
  const pendingNotifications  = filteredNotifications.filter(n => ['pending','queued','running'].includes(n.status));
  const readCount             = filteredNotifications.filter(n => Boolean(n.seen_at)).length;

  const handleTabChange = (_: React.SyntheticEvent, v: number) => {
    setActiveTab(v);
    setSearchParams({ status: ['all','success','failed','pending'][v] });
  };

  const handleStatusFilterChange = (newStatus: string) => {
    setPage(1);
    const params = new URLSearchParams(searchParams);
    newStatus === 'all' ? params.delete('status') : params.set('status', newStatus);
    setSearchParams(params);
  };

  const currentStatusFilter = searchParams.get('status') || 'all';
  const formatDate = (s: string) => new Date(s).toLocaleString();

  if (loading) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100%', display: 'grid', placeItems: 'center', pt: 8 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100%' }}>
      {/* ── Page header band ───────────────────────────────────── */}
      <Box sx={{ bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', px: { xs: 2, md: 3 }, pt: 2.5, pb: 2 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.75 }}>
          Console › Notifications
        </Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4">Notifications</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              Monitor and manage your email notifications
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexShrink={0}>
            {failedNotifications.length > 0 && (
              <Button
                variant="outlined"
                color="warning"
                startIcon={<ReplayIcon sx={{ fontSize: 15 }} />}
                onClick={() => void handleRetryMultiple(failedNotifications.map(n => n.id))}
                size="small"
              >
                Retry failed ({failedNotifications.length})
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<RefreshIcon sx={{ fontSize: 15 }} />}
              onClick={() => void fetchNotifications(true)}
              disabled={refreshing}
              size="small"
            >
              Refresh
            </Button>
          </Stack>
        </Stack>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip size="small" variant="outlined" label={`${filteredNotifications.length} total`} />
          <Chip size="small" variant="outlined" label={`${successNotifications.length} success`} color="success" />
          {failedNotifications.length > 0 && (
            <Chip size="small" variant="outlined" label={`${failedNotifications.length} failed`} color="error" />
          )}
          <Chip size="small" variant="outlined" label={`${readCount} read`} />
        </Stack>
      </Box>

      {refreshing && <LinearProgress />}

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

        {/* All-in-one content panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
          {/* Tab bar */}
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label={<Stack direction="row" spacing={1} alignItems="center"><span>All</span><Chip label={filteredNotifications.length} size="small" variant="outlined" /></Stack>} />
            <Tab label={<Stack direction="row" spacing={1} alignItems="center"><CheckCircleIcon sx={{ fontSize: 14 }} /><span>Success</span><Chip label={successNotifications.length} size="small" variant="outlined" /></Stack>} />
            <Tab label={<Stack direction="row" spacing={1} alignItems="center"><ErrorIcon sx={{ fontSize: 14 }} /><span>Failed</span><Chip label={failedNotifications.length} size="small" variant="outlined" /></Stack>} />
            <Tab label={<Stack direction="row" spacing={1} alignItems="center"><PendingIcon sx={{ fontSize: 14 }} /><span>Pending</span><Chip label={pendingNotifications.length} size="small" variant="outlined" /></Stack>} />
          </Tabs>

          {/* Filter bar */}
          <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper', display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
            <TextField
              size="small"
              placeholder="Search by email or template…"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              sx={{ flex: 1, minWidth: 220, maxWidth: 380 }}
              InputProps={{ startAdornment: <SearchIcon sx={{ mr: 0.75, fontSize: 16, color: 'text.secondary' }} /> }}
            />
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Status</InputLabel>
              <Select value={currentStatusFilter} onChange={e => handleStatusFilterChange(e.target.value as string)} label="Status">
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="success">Success</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="queued">Queued</MenuItem>
                <MenuItem value="running">Running</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              size="small"
              startIcon={<FilterListIcon sx={{ fontSize: 14 }} />}
              onClick={() => { setSearchTerm(''); handleStatusFilterChange('all'); }}
            >
              Clear filters
            </Button>
          </Box>

          {/* Table */}
          {filteredNotifications.length === 0 ? (
            <Box sx={{ py: 6, textAlign: 'center' }}>
              <EmailIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1.5 }} />
              <Typography variant="h6" color="text.secondary">No notifications found</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {searchTerm ? 'Try adjusting your search criteria' : 'No notifications have been sent yet'}
              </Typography>
            </Box>
          ) : (
            <>
              <TableContainer component={Paper} sx={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Template</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Seen</TableCell>
                      <TableCell>Executed at</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {paginatedNotifications.map((n) => (
                      <React.Fragment key={n.id}>
                        <TableRow
                          hover
                          onClick={() => toggleRow(n.id)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace', color: 'primary.main' }}>
                              #{n.id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>{n.template_id}</Typography>
                          </TableCell>
                          <TableCell sx={{ maxWidth: 240 }}>
                            <Typography variant="body2" noWrap title={n.email}>{n.email}</Typography>
                          </TableCell>
                          <TableCell>{getStatusChip(n.status)}</TableCell>
                          <TableCell>
                            <Chip
                              size="small"
                              label={n.seen_at ? 'Read' : 'Unread'}
                              variant="outlined"
                              color={n.seen_at ? 'default' : 'primary'}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">{formatDate(n.executed_at)}</Typography>
                          </TableCell>
                          <TableCell onClick={(e) => e.stopPropagation()}>
                            <Stack direction="row" spacing={1.5}>
                              <Tooltip title={n.seen_at ? 'Mark unread' : 'Mark read'}>
                                <IconButton size="small" onClick={() => void handleMarkSeen(n.id, !n.seen_at)}>
                                  {n.seen_at ? <MarkEmailUnreadIcon sx={{ fontSize: 16 }} /> : <MarkEmailReadIcon sx={{ fontSize: 16 }} />}
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Details">
                                <IconButton size="small" onClick={() => toggleRow(n.id)}>
                                  {expandedRows.has(n.id) ? <ExpandLessIcon sx={{ fontSize: 16 }} /> : <ExpandMoreIcon sx={{ fontSize: 16 }} />}
                                </IconButton>
                              </Tooltip>
                              {n.status === 'failed' && (
                                <Tooltip title="Retry">
                                  <IconButton size="small" onClick={() => void handleRetry(n.id)} disabled={retryLoading === n.id} color="error">
                                    {retryLoading === n.id ? <CircularProgress size={14} /> : <ReplayIcon sx={{ fontSize: 16 }} />}
                                  </IconButton>
                                </Tooltip>
                              )}
                              <Tooltip title="Resend">
                                <IconButton size="small" onClick={() => void handleResend(n.id)} disabled={resendLoading === n.id} color="primary">
                                  {resendLoading === n.id ? <CircularProgress size={14} /> : <EmailIcon sx={{ fontSize: 16 }} />}
                                </IconButton>
                              </Tooltip>
                            </Stack>
                          </TableCell>
                        </TableRow>

                        {/* Expandable detail row */}
                        <TableRow>
                          <TableCell sx={{ p: 0, border: 0 }} colSpan={7}>
                            <Collapse in={expandedRows.has(n.id)} timeout="auto" unmountOnExit>
                              <Box sx={{ bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', px: 3, py: 2, maxWidth: '100%', overflow: 'hidden' }}>
                                <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1.5, display: 'block' }}>
                                  Notification details
                                </Typography>
                                <Grid container spacing={2}>
                                  {[
                                    { label: 'Template ID',  value: n.template_id },
                                    { label: 'Email',        value: n.email },
                                    { label: 'Executed at',  value: formatDate(n.executed_at) },
                                    { label: 'Seen',         value: n.seen_at ? formatDate(n.seen_at) : 'Unread' },
                                    { label: 'Execution run',value: n.execution_run_id || '—', mono: true },
                                  ].map(row => (
                                    <Grid item xs={12} sm={6} md={4} key={row.label}>
                                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.25 }}>{row.label}</Typography>
                                      <Typography variant="body2" sx={{ fontWeight: 500, fontFamily: row.mono ? 'monospace' : undefined, wordBreak: 'break-all' }}>{row.value}</Typography>
                                    </Grid>
                                  ))}
                                  <Grid item xs={12} sm={6} md={4}>
                                    <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.25 }}>Status</Typography>
                                    {getStatusChip(n.status)}
                                  </Grid>
                                </Grid>
                                {n.error_message && (
                                  <Alert severity="error" sx={{ mt: 1.5 }}>
                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{n.error_message}</Typography>
                                  </Alert>
                                )}
                                {n.payload && Object.keys(n.payload).length > 0 && (
                                  <Box sx={{ mt: 1.5 }}>
                                    <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>Payload</Typography>
                                    <Box
                                      component="pre"
                                      sx={{
                                        m: 0, p: 1.5,
                                        bgcolor: 'background.default',
                                        border: '1px solid',
                                        borderColor: 'divider',
                                        borderRadius: 1,
                                        fontFamily: 'monospace',
                                        fontSize: '0.75rem',
                                        color: 'text.primary',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        maxHeight: 320,
                                        overflowY: 'auto',
                                      }}
                                    >
                                      {JSON.stringify(n.payload, null, 2)}
                                    </Box>
                                  </Box>
                                )}
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      </React.Fragment>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Pagination */}
              {computedTotalPages > 1 && (
                <Box sx={{ px: 2, py: 1.5, borderTop: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'flex-end' }}>
                  <Pagination count={computedTotalPages} page={page} onChange={(_, p) => setPage(p)} size="small" />
                </Box>
              )}
            </>
          )}
        </Box>
      </Box>

      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={() => setSnackbar(s => ({ ...s, open: false }))}>
        <Alert onClose={() => setSnackbar(s => ({ ...s, open: false }))} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Notifications;
