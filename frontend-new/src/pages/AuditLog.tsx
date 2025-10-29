import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Collapse,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  Pagination,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Search as SearchIcon,
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  email_to: string | null;
  template_id: string | null;
  payload: any;
  status: string | null;
  error_message: string | null;
  ip_address: string | null;
  created_at: string;
}

const AuditLogPage: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(20);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    };
  };

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/audit-logs?limit=1000&offset=0`,
        getAuthHeaders()
      );
      setAuditLogs(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const toggleRowExpansion = (id: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const getStatusIcon = (status: string | null) => {
    if (!status) return undefined;
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'pending':
        return <ScheduleIcon color="warning" />;
      default:
        return undefined;
    }
  };

  const getStatusColor = (status: string | null) => {
    if (!status) return 'default';
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const filteredLogs = auditLogs.filter(
    (log) =>
      log.email_to?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.template_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const paginatedLogs = filteredLogs.slice(
    (page - 1) * rowsPerPage,
    page * rowsPerPage
  );

  const totalPages = Math.ceil(filteredLogs.length / rowsPerPage);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            Audit Log
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Track all email activities and API usage
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <TextField
            fullWidth
            placeholder="Search by email, template, or action..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell width="50px">ID</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Template</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Details</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedLogs.map((log) => (
                  <React.Fragment key={log.id}>
                    <TableRow hover>
                      <TableCell>#{log.id}</TableCell>
                      <TableCell>
                        <Chip label={log.action} size="small" />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <EmailIcon fontSize="small" color="action" />
                          {log.email_to || 'N/A'}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <code>{log.template_id || 'N/A'}</code>
                      </TableCell>
                      <TableCell>
                        {log.status && (
                          <Chip
                            icon={getStatusIcon(log.status)}
                            label={log.status}
                            size="small"
                            color={getStatusColor(log.status) as any}
                          />
                        )}
                      </TableCell>
                      <TableCell>{formatDate(log.created_at)}</TableCell>
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => toggleRowExpansion(log.id)}
                          >
                            {expandedRows.has(log.id) ? (
                              <ExpandLessIcon />
                            ) : (
                              <ExpandMoreIcon />
                            )}
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={7}>
                        <Collapse in={expandedRows.has(log.id)} timeout="auto" unmountOnExit>
                          <Box sx={{ margin: 2 }}>
                            <Typography variant="subtitle2" gutterBottom>
                              Details
                            </Typography>
                            <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                              <Typography variant="body2">
                                <strong>Payload:</strong>
                              </Typography>
                              <pre style={{ fontSize: '0.875rem', marginTop: 8 }}>
                                {JSON.stringify(log.payload, null, 2)}
                              </pre>
                              {log.error_message && (
                                <>
                                  <Typography variant="body2" sx={{ mt: 2 }}>
                                    <strong>Error:</strong>
                                  </Typography>
                                  <Alert severity="error" sx={{ mt: 1 }}>
                                    {log.error_message}
                                  </Alert>
                                </>
                              )}
                              {log.ip_address && (
                                <Typography variant="body2" sx={{ mt: 1 }}>
                                  <strong>IP Address:</strong> {log.ip_address}
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {totalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AuditLogPage;

