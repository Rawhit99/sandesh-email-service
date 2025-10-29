import React, { useEffect, useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  Skeleton,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Send as SendIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiService, { Stats } from '../services/api';
import SendNotificationDialog from '../components/SendNotificationDialog';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>({
    total_notifications: 0,
    total_templates: 0,
    notifications_24h: 0,
    success_rate: 0,
    status_counts: {},
    success_count: 0,
    failed_count: 0,
    pending_count: 0,
    recent_notifications: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSendDialogOpen, setIsSendDialogOpen] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching stats...');
      const statsData = await apiService.getStats();
      console.log('Stats data received:', statsData);
      setStats(statsData);
    } catch (err) {
      console.error('Dashboard data fetch error:', err);
      setError('Failed to fetch dashboard data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSendSuccess = () => {
    fetchData();
  };

  const handleStatCardClick = (filter: string) => {
    navigate(`/notifications?status=${filter}`);
  };

  const StatCard: React.FC<{
    title: string;
    value: number | string;
    icon: React.ReactNode;
    color?: string;
    filter?: string;
    subtitle?: string;
  }> = ({ title, value, icon, color = 'primary', filter, subtitle }) => {
    // Get color values for the gradient
    const getColorValues = (colorName: string) => {
      switch (colorName) {
        case 'primary':
          return { 
            light: '#3b82f6', 
            main: '#2563eb',
            bg: '#eff6ff',
            iconBg: '#dbeafe'
          };
        case 'success':
          return { 
            light: '#34d399', 
            main: '#10b981',
            bg: '#ecfdf5',
            iconBg: '#d1fae5'
          };
        case 'error':
          return { 
            light: '#f87171', 
            main: '#ef4444',
            bg: '#fef2f2',
            iconBg: '#fecaca'
          };
        case 'warning':
          return { 
            light: '#fbbf24', 
            main: '#f59e0b',
            bg: '#fffbeb',
            iconBg: '#fef3c7'
          };
        default:
          return { 
            light: '#3b82f6', 
            main: '#2563eb',
            bg: '#eff6ff',
            iconBg: '#dbeafe'
          };
      }
    };

    const colors = getColorValues(color);

    return (
      <Card 
        sx={{ 
          cursor: filter ? 'pointer' : 'default',
          '&:hover': filter ? { 
            transform: 'translateY(-4px)',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            transition: 'all 0.3s ease-in-out'
          } : {},
          height: '100%',
          background: 'white',
          border: `1px solid ${colors.iconBg}`,
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.2s ease-in-out',
        }}
        onClick={() => filter && handleStatCardClick(filter)}
      >
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box sx={{ 
              bgcolor: colors.iconBg, 
              width: 48, 
              height: 48, 
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Box sx={{ color: colors.main, fontSize: '1.5rem' }}>
                {icon}
              </Box>
            </Box>
            {filter && (
              <Box sx={{ 
                bgcolor: colors.bg,
                color: colors.main,
                px: 1.5,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.75rem',
                fontWeight: 600,
              }}>
                View All
              </Box>
            )}
          </Box>
          
          <Box>
            <Typography 
              variant="h3" 
              component="div" 
              sx={{ 
                fontWeight: 700, 
                mb: 1,
                color: 'text.primary',
                fontSize: '2.25rem',
                lineHeight: 1,
              }}
            >
              {value}
            </Typography>
            <Typography 
              variant="h6" 
              sx={{ 
                color: 'text.primary',
                fontWeight: 600,
                fontSize: '1rem',
                mb: 0.5,
              }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'text.secondary',
                  fontSize: '0.875rem',
                }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Box p={3}>
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item}>
              <Skeleton variant="rectangular" height={120} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
          <Box>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1, color: 'text.primary' }}>
              Welcome back! 👋
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ fontSize: '1.1rem' }}>
              Here's what's happening with your email notifications today
            </Typography>
          </Box>
          <Box display="flex" gap={2} alignItems="center">
            <Tooltip title="Refresh Data">
              <IconButton 
                onClick={fetchData} 
                color="primary"
                sx={{ 
                  bgcolor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    bgcolor: 'primary.dark',
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.2s ease-in-out'
                }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              size="large"
              startIcon={<SendIcon />}
              onClick={() => setIsSendDialogOpen(true)}
              sx={{ 
                borderRadius: 2,
                px: 3,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                },
                transition: 'all 0.2s ease-in-out',
              }}
            >
              Send Email
            </Button>
          </Box>
        </Box>

        {/* Status Cards Row */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1, 
            px: 2, 
            py: 1, 
            bgcolor: 'success.main', 
            color: 'white', 
            borderRadius: 2,
            fontSize: '0.875rem',
            fontWeight: 600
          }}>
            <CheckCircleIcon sx={{ fontSize: 16 }} />
            System Online
          </Box>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1, 
            px: 2, 
            py: 1, 
            bgcolor: 'primary.main', 
            color: 'white', 
            borderRadius: 2,
            fontSize: '0.875rem',
            fontWeight: 600
          }}>
            <EmailIcon sx={{ fontSize: 16 }} />
            {stats.total_templates} Templates
          </Box>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1, 
            px: 2, 
            py: 1, 
            bgcolor: 'warning.main', 
            color: 'white', 
            borderRadius: 2,
            fontSize: '0.875rem',
            fontWeight: 600
          }}>
            <ScheduleIcon sx={{ fontSize: 16 }} />
            {stats.pending_count} Pending
          </Box>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
          {success}
        </Alert>
      )}

      {/* Email Count Stats */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Emails"
            value={stats.total_notifications}
            icon={<EmailIcon />}
            color="primary"
            filter="all"
            subtitle="All time"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Successful"
            value={stats.success_count}
            icon={<CheckCircleIcon />}
            color="success"
            filter="success"
            subtitle="Delivered"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Failed"
            value={stats.failed_count}
            icon={<ErrorIcon />}
            color="error"
            filter="failed"
            subtitle="Needs retry"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending"
            value={stats.pending_count}
            icon={<ScheduleIcon />}
            color="warning"
            filter="pending"
            subtitle="In queue"
          />
        </Grid>
      </Grid>

      {/* Quick Actions Section */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)', border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ p: 4 }}>
              <Box display="flex" alignItems="center" mb={3}>
                <Box sx={{ 
                  bgcolor: 'primary.main', 
                  width: 40, 
                  height: 40, 
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mr: 2
                }}>
                  <SendIcon sx={{ color: 'white', fontSize: '1.25rem' }} />
                </Box>
                <Box>
                  <Typography variant="h5" component="h2" sx={{ fontWeight: 700, color: 'text.primary', mb: 0.5 }}>
                    Send New Email
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Create and send email notifications instantly
                  </Typography>
                </Box>
              </Box>
              
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.6 }}>
                Use your templates to send personalized emails to your users. Track delivery status and manage your campaigns efficiently.
              </Typography>
              
              <Button
                variant="contained"
                size="large"
                startIcon={<SendIcon />}
                onClick={() => setIsSendDialogOpen(true)}
                sx={{ 
                  borderRadius: 2,
                  py: 1.5,
                  px: 4,
                  fontSize: '1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                Send New Email
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', background: 'white', border: '1px solid #e2e8f0' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'text.primary' }}>
                Quick Stats
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ 
                    bgcolor: '#eff6ff', 
                    width: 32, 
                    height: 32, 
                    borderRadius: 1.5,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <EmailIcon sx={{ fontSize: 16, color: 'primary.main' }} />
                  </Box>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                      {stats.total_templates}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Templates
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ 
                    bgcolor: '#ecfdf5', 
                    width: 32, 
                    height: 32, 
                    borderRadius: 1.5,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
                  </Box>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                      {stats.success_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Sent Today
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ 
                    bgcolor: '#fffbeb', 
                    width: 32, 
                    height: 32, 
                    borderRadius: 1.5,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <ScheduleIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                  </Box>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary' }}>
                      {stats.pending_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Pending
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Send Email Dialog */}
      <SendNotificationDialog
        open={isSendDialogOpen}
        onClose={() => setIsSendDialogOpen(false)}
        onSuccess={handleSendSuccess}
      />
    </Box>
  );
};

export default Dashboard;