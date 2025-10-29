import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
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
  CircularProgress,
  Alert,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Avatar,
  Collapse,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  Refresh as RefreshIcon,
  Replay as ReplayIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  FilterList as FilterListIcon,
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { useSearchParams } from 'react-router-dom';
import apiService, { Notification } from '../services/api';

const EmailStatus: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') || 'all';
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [retryingId, setRetryingId] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(10);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      const data = await apiService.getNotifications({ status: statusFilter });
      setNotifications(data);
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [statusFilter]);

  const handleRetry = async (notificationId: number) => {
    try {
      setRetryingId(notificationId);
      setError(null);
      setSuccess(null);
      await apiService.retryNotification(notificationId);
      setSuccess('Notification retry initiated successfully');
      setTimeout(fetchNotifications, 1000);
    } catch (err) {
      console.error('Error retrying notification:', err);
      setError('Failed to retry notification');
    } finally {
      setRetryingId(null);
    }
  };

  const handleRetryMultiple = async (notificationIds: number[]) => {
    try {
      setError(null);
      setSuccess(null);
      
      const promises = notificationIds.map(id => apiService.retryNotification(id));
      await Promise.all(promises);
      
      setSuccess(`Successfully retried ${notificationIds.length} notifications`);
      setTimeout(fetchNotifications, 1000);
    } catch (err) {
      console.error('Error retrying notifications:', err);
      setError('Failed to retry some notifications');
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <Chip
            icon={<CheckCircleIcon />}
            label="Success"
            color="success"
            size="small"
            variant="filled"
          />
        );
      case 'failed':
        return (
          <Chip
            icon={<ErrorIcon />}
            label="Failed"
            color="error"
            size="small"
            variant="filled"
          />
        );
      case 'pending':
        return (
          <Chip
            icon={<PendingIcon />}
            label="Pending"
            color="warning"
            size="small"
            variant="filled"
          />
        );
      default:
        return (
          <Chip
            label={status}
            size="small"
            variant="outlined"
          />
        );
    }
  };

  const toggleRowExpansion = (id: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const filteredNotifications = notifications.filter(notification =>
    notification.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    notification.template_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const paginatedNotifications = filteredNotifications.slice(
    (page - 1) * rowsPerPage,
    page * rowsPerPage
  );

  const failedNotifications = filteredNotifications.filter(n => n.status === 'failed');

  const pageTitle = statusFilter !== 'all'
    ? `Email Notifications - ${statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)}`
    : 'Email Notifications';

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            {pageTitle}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and manage your email notifications
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchNotifications} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          {failedNotifications.length > 0 && (
            <Button
              variant="contained"
              color="error"
              startIcon={<ReplayIcon />}
              onClick={() => handleRetryMultiple(failedNotifications.map(n => n.id))}
            >
              Retry All Failed ({failedNotifications.length})
            </Button>
          )}
        </Box>
      </Box>

      {/* Filters and Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search by email or template..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status Filter</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setSearchParams({ status: e.target.value })}
                  label="Status Filter"
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="success">Success</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={5}>
              <Box display="flex" gap={1}>
                <Chip label={`Total: ${filteredNotifications.length}`} color="primary" />
                <Chip label={`Success: ${filteredNotifications.filter(n => n.status === 'success').length}`} color="success" />
                <Chip label={`Failed: ${filteredNotifications.filter(n => n.status === 'failed').length}`} color="error" />
                <Chip label={`Pending: ${filteredNotifications.filter(n => n.status === 'pending').length}`} color="warning" />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      ) : filteredNotifications.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <EmailIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No notifications found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchTerm ? 'Try adjusting your search criteria' : 'No notifications have been sent yet'}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <>
          <TableContainer component={Paper} sx={{ mb: 2 }}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: 'grey.50' }}>
                  <TableCell>ID</TableCell>
                  <TableCell>Template</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Executed At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedNotifications.map((notification) => (
                  <React.Fragment key={notification.id}>
                    <TableRow hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          #{notification.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {notification.template_id}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: 'primary.main' }}>
                            {notification.email.charAt(0).toUpperCase()}
                          </Avatar>
                          <Typography variant="body2">
                            {notification.email}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {getStatusChip(notification.status)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(notification.executed_at).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={1}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => toggleRowExpansion(notification.id)}
                            >
                              {expandedRows.has(notification.id) ? 
                                <ExpandLessIcon /> : <ExpandMoreIcon />
                              }
                            </IconButton>
                          </Tooltip>
                          {notification.status === 'failed' && (
                            <Tooltip title="Retry">
                              <IconButton
                                size="small"
                                onClick={() => handleRetry(notification.id)}
                                disabled={retryingId === notification.id}
                                color="error"
                              >
                                {retryingId === notification.id ? (
                                  <CircularProgress size={20} />
                                ) : (
                                  <ReplayIcon />
                                )}
                              </IconButton>
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                        <Collapse in={expandedRows.has(notification.id)} timeout="auto" unmountOnExit>
                          <Box sx={{ margin: 1 }}>
                            <Card variant="outlined">
                              <CardContent>
                                <Typography variant="h6" gutterBottom>
                                  Notification Details
                                </Typography>
                                <Grid container spacing={2}>
                                  <Grid item xs={12} md={6}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                      Template ID
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      {notification.template_id}
                                    </Typography>
                                  </Grid>
                                  <Grid item xs={12} md={6}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                      Email Address
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      {notification.email}
                                    </Typography>
                                  </Grid>
                                  <Grid item xs={12} md={6}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                      Status
                                    </Typography>
                                    {getStatusChip(notification.status)}
                                  </Grid>
                                  <Grid item xs={12} md={6}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                      Executed At
                                    </Typography>
                                    <Typography variant="body2" gutterBottom>
                                      {new Date(notification.executed_at).toLocaleString()}
                                    </Typography>
                                  </Grid>
                                  {notification.error_message && (
                                    <Grid item xs={12}>
                                      <Typography variant="subtitle2" color="text.secondary">
                                        Error Message
                                      </Typography>
                                      <Alert severity="error" sx={{ mt: 1 }}>
                                        {notification.error_message}
                                      </Alert>
                                    </Grid>
                                  )}
                                  {notification.payload && Object.keys(notification.payload).length > 0 && (
                                    <Grid item xs={12}>
                                      <Typography variant="subtitle2" color="text.secondary">
                                        Payload Data
                                      </Typography>
                                      <Box sx={{ 
                                        bgcolor: 'grey.50', 
                                        p: 2, 
                                        borderRadius: 1,
                                        fontFamily: 'monospace',
                                        fontSize: '0.875rem'
                                      }}>
                                        {JSON.stringify(notification.payload, null, 2)}
                                      </Box>
                                    </Grid>
                                  )}
                                </Grid>
                              </CardContent>
                            </Card>
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
          <Box display="flex" justifyContent="center" mt={3}>
            <Pagination
              count={Math.ceil(filteredNotifications.length / rowsPerPage)}
              page={page}
              onChange={(e, newPage) => setPage(newPage)}
              color="primary"
              showFirstButton
              showLastButton
            />
          </Box>
        </>
      )}
    </Box>
  );
};

export default EmailStatus; 