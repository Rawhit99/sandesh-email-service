import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  LinearProgress,
  Pagination,
  Paper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Block as BlockIcon,
  CheckCircle as ActivateIcon,
  Edit as EditIcon,
  Group as GroupIcon,
  PersonAdd as PersonAddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiService, { Subscriber } from '../services/api';

const getDataString = (data: Subscriber['data'], key: string): string => {
  const value = data?.[key];
  return typeof value === 'string' ? value : '';
};

const formatSubscriberName = (subscriber: Subscriber): string => {
  const firstName = getDataString(subscriber.data, 'firstName').trim();
  const lastName = getDataString(subscriber.data, 'lastName').trim();
  return [firstName, lastName].filter(Boolean).join(' ') || '-';
};

const formatProfileData = (data: Subscriber['data']): string => {
  if (!data) {
    return '-';
  }
  const entries = Object.entries(data).filter(([key, value]) => {
    if (key === 'firstName' || key === 'lastName') {
      return false;
    }
    return value !== null && value !== undefined && String(value).trim() !== '';
  });
  if (entries.length === 0) {
    return '-';
  }
  return entries
    .map(([key, value]) => `${key}: ${typeof value === 'object' ? JSON.stringify(value) : String(value)}`)
    .join(', ');
};

const Subscribers: React.FC = () => {
  const [rows, setRows] = useState<Subscriber[]>([]);
  const [subscriberId, setSubscriberId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [editOpen, setEditOpen]   = useState(false);
  const [editSid, setEditSid]     = useState('');
  const [editFirstName, setEditFirstName] = useState('');
  const [editLastName, setEditLastName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editData, setEditData] = useState<Record<string, any>>({});
  const [editActive, setEditActive] = useState(true);
  const [page, setPage]           = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const rowsPerPage               = 10;

  const load = useCallback(async (background = false) => {
    try {
      background ? setRefreshing(true) : setLoading(true);
      const data = await apiService.listSubscribers();
      setRows(data);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load subscribers');
    } finally {
      background ? setRefreshing(false) : setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleCreate = async () => {
    setError(null);
    try {
      setRefreshing(true);
      const data = {
        ...(firstName.trim() ? { firstName: firstName.trim() } : {}),
        ...(lastName.trim() ? { lastName: lastName.trim() } : {}),
      };
      await apiService.createSubscriber({
        subscriber_id: subscriberId.trim(),
        email: email.trim(),
        data: Object.keys(data).length ? data : undefined,
      });
      setSubscriberId('');
      setFirstName('');
      setLastName('');
      setEmail('');
      setSuccess('Subscriber created');
      await load(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Create failed');
    } finally {
      setRefreshing(false);
    }
  };

  const handleSaveEdit = async () => {
    try {
      const nextData = { ...editData };
      if (editFirstName.trim()) {
        nextData.firstName = editFirstName.trim();
      } else {
        delete nextData.firstName;
      }
      if (editLastName.trim()) {
        nextData.lastName = editLastName.trim();
      } else {
        delete nextData.lastName;
      }
      await apiService.updateSubscriber(editSid, {
        email: editEmail.trim(),
        data: nextData,
        is_active: editActive,
      });
      setEditOpen(false);
      setSuccess('Subscriber updated');
      await load(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Update failed');
    }
  };

  const handleDeactivate = async (id: string) => {
    try {
      await apiService.deactivateSubscriber(id);
      await load(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Deactivate failed');
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await apiService.activateSubscriber(id);
      await load(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Activate failed');
    }
  };

  if (loading) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100%', display: 'grid', placeItems: 'center', pt: 8 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  const filteredRows = rows.filter((r) => {
    const q = searchTerm.trim().toLowerCase();
    if (!q) return true;
    return (
      r.subscriber_id.toLowerCase().includes(q) ||
      r.email.toLowerCase().includes(q) ||
      formatSubscriberName(r).toLowerCase().includes(q) ||
      formatProfileData(r.data).toLowerCase().includes(q)
    );
  });
  const activeCount      = rows.filter(r => r.is_active).length;
  const totalPages       = Math.max(1, Math.ceil(filteredRows.length / rowsPerPage));
  const paginatedRows    = filteredRows.slice((page - 1) * rowsPerPage, page * rowsPerPage);

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100%' }}>
      {/* ── Page header band ─────────────────────────────────────── */}
      <Box sx={{ bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', px: { xs: 2, md: 3 }, pt: 2.5, pb: 2 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.75 }}>
          Console › Subscribers
        </Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4">Subscribers</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              When <code>SUBSCRIBER_REQUIRED</code> is enabled, only listed profiles receive sends
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon sx={{ fontSize: 15 }} />}
            onClick={() => void load(true)}
            disabled={refreshing}
            size="small"
          >
            Refresh
          </Button>
        </Stack>
        <Box sx={{ mt: 1.5 }}>
          <TextField
            size="small"
            placeholder="Search by subscriber id, name, email, profile data..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            sx={{ width: { xs: '100%', md: 420 } }}
          />
        </Box>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip size="small" variant="outlined" label={`${rows.length} total`} />
          <Chip size="small" variant="outlined" label={`${activeCount} active`} color="success" />
          {rows.length - activeCount > 0 && (
            <Chip size="small" variant="outlined" label={`${rows.length - activeCount} inactive`} />
          )}
        </Stack>
      </Box>

      {refreshing && <LinearProgress />}

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

        {/* Create panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 2.5, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Add subscriber</Typography>
          <Stack direction="row" spacing={1.5} flexWrap="wrap" alignItems="flex-end">
            <TextField
              label="Subscriber ID"
              value={subscriberId}
              onChange={(e) => setSubscriberId(e.target.value)}
              size="small"
              sx={{ minWidth: 200 }}
            />
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              size="small"
              sx={{ minWidth: 260 }}
            />
            <TextField
              label="First name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              size="small"
              sx={{ minWidth: 180 }}
            />
            <TextField
              label="Last name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              size="small"
              sx={{ minWidth: 180 }}
            />
            <Button
              variant="contained"
              startIcon={<PersonAddIcon sx={{ fontSize: 15 }} />}
              onClick={() => void handleCreate()}
              disabled={refreshing || !subscriberId.trim() || !email.trim()}
              size="small"
            >
              Add subscriber
            </Button>
          </Stack>
        </Box>

        {/* Table panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
          {filteredRows.length === 0 ? (
            <Box sx={{ py: 8, textAlign: 'center' }}>
              <GroupIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1.5 }} />
              <Typography variant="h6" color="text.secondary">No subscribers yet</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Add your first subscriber using the form above
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} sx={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Subscriber ID</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Profile Data</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedRows.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>
                        <Box component="code" sx={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: 'primary.main' }}>
                          {r.subscriber_id}
                        </Box>
                      </TableCell>
                      <TableCell><Typography variant="body2">{formatSubscriberName(r)}</Typography></TableCell>
                      <TableCell><Typography variant="body2">{r.email}</Typography></TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 260 }}>
                          {formatProfileData(r.data)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          variant="outlined"
                          label={r.is_active ? 'Active' : 'Inactive'}
                          color={r.is_active ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="Edit">
                            <IconButton size="small" onClick={() => { setEditSid(r.subscriber_id); setEditFirstName(getDataString(r.data, 'firstName')); setEditLastName(getDataString(r.data, 'lastName')); setEditEmail(r.email); setEditData(r.data ?? {}); setEditActive(r.is_active); setEditOpen(true); }}>
                              <EditIcon sx={{ fontSize: 16 }} />
                            </IconButton>
                          </Tooltip>
                          {r.is_active && (
                            <Tooltip title="Deactivate">
                              <IconButton size="small" color="warning" onClick={() => void handleDeactivate(r.subscriber_id)}>
                                <BlockIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>
                          )}
                          {!r.is_active && (
                            <Tooltip title="Activate">
                              <IconButton size="small" color="success" onClick={() => void handleActivate(r.subscriber_id)}>
                                <ActivateIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          {totalPages > 1 && (
            <Box sx={{ px: 2, py: 1.5, borderTop: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'flex-end' }}>
              <Pagination count={totalPages} page={page} onChange={(_, p) => setPage(p)} size="small" />
            </Box>
          )}
        </Box>
      </Box>

      {/* ── Edit dialog ─────────────────────────────────────────── */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Edit subscriber</DialogTitle>
        <DialogContent>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1.5, fontFamily: 'monospace' }}>
            {editSid}
          </Typography>
          <TextField fullWidth margin="dense" label="First name" value={editFirstName} onChange={e => setEditFirstName(e.target.value)} size="small" />
          <TextField fullWidth margin="dense" label="Last name" value={editLastName} onChange={e => setEditLastName(e.target.value)} size="small" />
          <TextField fullWidth margin="dense" label="Email" type="email" value={editEmail} onChange={e => setEditEmail(e.target.value)} size="small" />
          <FormControlLabel
            control={<Switch checked={editActive} onChange={e => setEditActive(e.target.checked)} size="small" />}
            label={<Typography variant="body2">Active</Typography>}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" size="small" onClick={() => setEditOpen(false)}>Cancel</Button>
          <Button variant="contained" size="small" onClick={() => void handleSaveEdit()}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Subscribers;
