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
  Edit as EditIcon,
  Group as GroupIcon,
  PersonAdd as PersonAddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiService, { Subscriber } from '../services/api';

const Subscribers: React.FC = () => {
  const [rows, setRows] = useState<Subscriber[]>([]);
  const [subscriberId, setSubscriberId] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [editOpen, setEditOpen]   = useState(false);
  const [editSid, setEditSid]     = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editActive, setEditActive] = useState(true);
  const [page, setPage]           = useState(1);
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
      await apiService.createSubscriber({ subscriber_id: subscriberId.trim(), email: email.trim() });
      setSubscriberId('');
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
      await apiService.updateSubscriber(editSid, { email: editEmail.trim(), is_active: editActive });
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

  if (loading) {
    return (
      <Box sx={{ bgcolor: 'background.default', minHeight: '100%', display: 'grid', placeItems: 'center', pt: 8 }}>
        <CircularProgress size={32} />
      </Box>
    );
  }

  const activeCount      = rows.filter(r => r.is_active).length;
  const totalPages       = Math.max(1, Math.ceil(rows.length / rowsPerPage));
  const paginatedRows    = rows.slice((page - 1) * rowsPerPage, page * rowsPerPage);

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
          {rows.length === 0 ? (
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
                    <TableCell>Email</TableCell>
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
                      <TableCell><Typography variant="body2">{r.email}</Typography></TableCell>
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
                            <IconButton size="small" onClick={() => { setEditSid(r.subscriber_id); setEditEmail(r.email); setEditActive(r.is_active); setEditOpen(true); }}>
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
