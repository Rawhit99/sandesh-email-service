import React, { useEffect, useState } from 'react';
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
  Button,
  Tabs,
  Tab,
  Snackbar,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  Refresh as RefreshIcon,
  Replay as ReplayIcon,
  Visibility as VisibilityIcon,
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Email as EmailIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import { useSearchParams } from 'react-router-dom';
import apiService, { Notification, NotificationFilters } from '../services/api';

const Notifications: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [page, setPage] = useState(1);
  const [rowsPerPage] = useState(10);
  const [retryingId, setRetryingId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [searchEmail, setSearchEmail] = useState('');
  const [retryLoading, setRetryLoading] = useState<number | null>(null);
  const [resendLoading, setResendLoading] = useState<number | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const limit = 20;

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const status = searchParams.get('status') || 'all';
      
      const data = await apiService.getNotifications({
        status,
        email: searchEmail || undefined,
      });
      
      setNotifications(data || []);
      // Since the API doesn't return pagination info, we'll show all results
      setTotalPages(1);
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [searchParams, searchEmail]);

  const handleRetry = async (notificationId: number) => {
    try {
      setRetryLoading(notificationId);
      await apiService.retryNotification(notificationId);
      setSnackbar({
        open: true,
        message: 'Email retry initiated successfully',
        severity: 'success'
      });
      // Refresh the list after a short delay
      setTimeout(() => {
        fetchNotifications();
      }, 1000);
    } catch (err) {
      console.error('Error retrying notification:', err);
      setSnackbar({
        open: true,
        message: 'Failed to retry email',
        severity: 'error'
      });
    } finally {
      setRetryLoading(null);
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

  const handleResend = async (notificationId: number) => {
    try {
      setResendLoading(notificationId);
      await apiService.resendNotification(notificationId);
      setSnackbar({
        open: true,
        message: 'Resend initiated successfully',
        severity: 'success'
      });
      setTimeout(() => {
        fetchNotifications();
      }, 1000);
    } catch (err) {
      console.error('Error resending notification:', err);
      setSnackbar({
        open: true,
        message: 'Failed to resend notification',
        severity: 'error'
      });
    } finally {
      setResendLoading(null);
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
  const successNotifications = filteredNotifications.filter(n => n.status === 'success');
  const pendingNotifications = filteredNotifications.filter(n => n.status === 'pending');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    const statusMap = ['all', 'success', 'failed', 'pending'];
    setSearchParams({ status: statusMap[newValue] });
  };

  const handleStatusFilterChange = (newStatus: string) => {
    setPage(1);
    const params = new URLSearchParams(searchParams);
    if (newStatus === 'all') {
      params.delete('status');
    } else {
      params.set('status', newStatus);
    }
    setSearchParams(params);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'pending':
        return <PendingIcon color="warning" />;
      default:
        return <PendingIcon />;
    }
  };

  const getStatusColor = (status: string) => {
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

  // Get current status filter from URL params
  const currentStatusFilter = searchParams.get('status') || 'all';

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            Notifications
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

      {/* Status Tabs */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 0 }}>
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            sx={{
              '& .MuiTab-root': {
                minHeight: 64,
                fontSize: '0.875rem',
                fontWeight: 600,
              },
            }}
          >
            <Tab 
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography>All</Typography>
                  <Chip label={filteredNotifications.length} size="small" color="primary" />
                </Box>
              } 
            />
            <Tab 
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <CheckCircleIcon fontSize="small" />
                  <Typography>Success</Typography>
                  <Chip label={successNotifications.length} size="small" color="success" />
                </Box>
              } 
            />
            <Tab 
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <ErrorIcon fontSize="small" />
                  <Typography>Failed</Typography>
                  <Chip label={failedNotifications.length} size="small" color="error" />
                </Box>
              } 
            />
            <Tab 
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <PendingIcon fontSize="small" />
                  <Typography>Pending</Typography>
                  <Chip label={pendingNotifications.length} size="small" color="warning" />
                </Box>
              } 
            />
          </Tabs>
        </CardContent>
      </Card>

      {/* Search and Filters */}
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
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Status Filter</InputLabel>
                <Select
                  value={currentStatusFilter}
                  onChange={(e) => handleStatusFilterChange(e.target.value)}
                  label="Status Filter"
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="success">Success</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Button
                variant="outlined"
                startIcon={<FilterListIcon />}
                onClick={() => {
                  setSearchTerm('');
                  handleStatusFilterChange('all');
                }}
                fullWidth
              >
                Clear Filters
              </Button>
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
                        <Box display="flex" alignItems="center" gap={1}>
                          {getStatusIcon(notification.status)}
                          <Chip
                            label={notification.status}
                            size="small"
                            color={getStatusColor(notification.status) as any}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(notification.executed_at)}
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
                                disabled={retryLoading === notification.id}
                                color="error"
                              >
                                {retryLoading === notification.id ? (
                                  <CircularProgress size={20} />
                                ) : (
                                  <ReplayIcon />
                                )}
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Resend">
                            <IconButton
                              size="small"
                              onClick={() => handleResend(notification.id)}
                              disabled={resendLoading === notification.id}
                              color="primary"
                            >
                              {resendLoading === notification.id ? (
                                <CircularProgress size={20} />
                              ) : (
                                <EmailIcon />
                              )}
                            </IconButton>
                          </Tooltip>
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
                                      {formatDate(notification.executed_at)}
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
        </>
      )}

      {/* Snackbar for retry feedback */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Notifications; 