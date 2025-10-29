import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Chip,
  Tooltip,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckCircleIcon,
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    };
  };

  const fetchApiKeys = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/api-keys`,
        getAuthHeaders()
      );
      setApiKeys(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const handleCreateKey = async () => {
    try {
      setLoading(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/api-keys`,
        {},
        getAuthHeaders()
      );
      setNewKey(response.data.key);
      setOpenDialog(true);
      fetchApiKeys();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create API key');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteKey = async (keyId: number) => {
    if (!window.confirm('Are you sure you want to delete this API key?')) {
      return;
    }

    try {
      setLoading(true);
      await axios.delete(
        `${API_BASE_URL}/api/v1/api-keys/${keyId}`,
        getAuthHeaders()
      );
      setSuccess('API key deleted successfully');
      fetchApiKeys();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete API key');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    setSuccess('API key copied to clipboard');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            API Keys
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage your API keys for accessing the email notification API
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateKey}
          disabled={loading}
        >
          Create API Key
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Key Prefix</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Last Used</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {apiKeys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell>
                      <code>{key.key_prefix}...</code>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={key.is_active ? 'Active' : 'Inactive'}
                        color={key.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{formatDate(key.created_at)}</TableCell>
                    <TableCell>
                      {key.last_used_at ? formatDate(key.last_used_at) : 'Never'}
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteKey(key.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>API Key Created</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Please copy this API key now. You won't be able to see it again!
          </Alert>
          <TextField
            fullWidth
            label="API Key"
            value={newKey || ''}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <IconButton onClick={() => newKey && handleCopyKey(newKey)}>
                  <CopyIcon />
                </IconButton>
              ),
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
        message={success}
      />
    </Box>
  );
};

export default ApiKeys;

