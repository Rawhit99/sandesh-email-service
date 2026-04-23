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
  IconButton,
  LinearProgress,
  Paper,
  Snackbar,
  Stack,
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
  Add as AddIcon,
  ContentCopy as CopyIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  VpnKey as KeyIcon,
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface APIKey {
  id: number;
  key_prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

const ApiKeys: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { headers: { Authorization: `Bearer ${token}` } };
  };

  const fetchApiKeys = useCallback(async (background = false) => {
    try {
      background ? setRefreshing(true) : setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/v1/api-keys`, getAuthHeaders());
      setApiKeys(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch API keys');
    } finally {
      background ? setRefreshing(false) : setLoading(false);
    }
  }, []);

  useEffect(() => { void fetchApiKeys(); }, [fetchApiKeys]);

  const handleCreateKey = async () => {
    try {
      setRefreshing(true);
      const response = await axios.post(`${API_BASE_URL}/api/v1/api-keys`, {}, getAuthHeaders());
      setNewKey(response.data.key);
      setOpenDialog(true);
      void fetchApiKeys(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create API key');
    } finally {
      setRefreshing(false);
    }
  };

  const handleDeleteKey = async (keyId: number) => {
    if (!window.confirm('Delete this API key? This cannot be undone.')) return;
    try {
      setRefreshing(true);
      await axios.delete(`${API_BASE_URL}/api/v1/api-keys/${keyId}`, getAuthHeaders());
      setSuccess('API key deleted');
      void fetchApiKeys(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete API key');
    } finally {
      setRefreshing(false);
    }
  };

  const handleCopyKey = (key: string) => {
    void navigator.clipboard.writeText(key);
    setSuccess('API key copied to clipboard');
  };

  const fmt = (s: string) => new Date(s).toLocaleString();

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
          Console › API Keys
        </Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4">API Keys</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              Manage API keys for programmatic access to Sandesh
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexShrink={0}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon sx={{ fontSize: 15 }} />}
              onClick={() => void fetchApiKeys(true)}
              disabled={refreshing}
              size="small"
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon sx={{ fontSize: 15 }} />}
              onClick={() => void handleCreateKey()}
              disabled={refreshing}
              size="small"
            >
              Create API key
            </Button>
          </Stack>
        </Stack>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip size="small" variant="outlined" label={`${apiKeys.length} total`} />
          <Chip size="small" variant="outlined" label={`${apiKeys.filter(k => k.is_active).length} active`} color="success" />
        </Stack>
      </Box>

      {refreshing && <LinearProgress />}

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

        {/* Table panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
          {apiKeys.length === 0 ? (
            <Box sx={{ py: 8, textAlign: 'center' }}>
              <KeyIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 1.5 }} />
              <Typography variant="h6" color="text.secondary">No API keys yet</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Create your first API key to start integrating with Sandesh
              </Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => void handleCreateKey()} sx={{ mt: 2 }} size="small">
                Create API key
              </Button>
            </Box>
          ) : (
            <TableContainer component={Paper} sx={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Key prefix</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created at</TableCell>
                    <TableCell>Last used</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {apiKeys.map((key) => (
                    <TableRow key={key.id} hover>
                      <TableCell>
                        <Box component="code" sx={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: 'primary.main', bgcolor: 'action.hover', px: 0.75, py: 0.25, borderRadius: 0.5 }}>
                          {key.key_prefix}…
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={key.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          variant="outlined"
                          color={key.is_active ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell><Typography variant="body2">{fmt(key.created_at)}</Typography></TableCell>
                      <TableCell>
                        <Typography variant="body2" color={key.last_used_at ? 'text.primary' : 'text.secondary'}>
                          {key.last_used_at ? fmt(key.last_used_at) : 'Never'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Delete key">
                          <IconButton size="small" color="error" onClick={() => void handleDeleteKey(key.id)}>
                            <DeleteIcon sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      </Box>

      {/* ── New key dialog ─────────────────────────────────────────── */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>API key created</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Copy this key now — you won't be able to see it again.
          </Alert>
          <TextField
            fullWidth
            label="API Key"
            value={newKey || ''}
            size="small"
            InputProps={{
              readOnly: true,
              sx: { fontFamily: 'monospace', fontSize: '0.8125rem' },
              endAdornment: (
                <IconButton size="small" onClick={() => newKey && handleCopyKey(newKey)}>
                  <CopyIcon sx={{ fontSize: 16 }} />
                </IconButton>
              ),
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" size="small" onClick={() => setOpenDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!success && !openDialog} autoHideDuration={4000} onClose={() => setSuccess(null)} message={success} />
    </Box>
  );
};

export default ApiKeys;
