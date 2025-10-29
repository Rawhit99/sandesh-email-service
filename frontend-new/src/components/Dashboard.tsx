import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  FormControlLabel,
  Switch,
  Skeleton,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Email as EmailIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import apiService, { 
  Stats, 
  Notification, 
  EmailTemplate, 
  TemplateCreate, 
  TemplateUpdate, 
  SESStatus, 
  TemplateCreateRequest,
  NotificationSummary,
} from '../services/api';
import SendNotificationDialog from './SendNotificationDialog';
import { useNavigate } from 'react-router-dom';

// Form data interface for editing templates
interface TemplateFormData {
  template_id: string;
  name: string;
  subject: string;
  content: string;
  variables: Record<string, string>; // For form editing with key-value pairs
  is_active: boolean;
}

// Utility functions for type conversion
const convertTemplateToFormData = (template: EmailTemplate): TemplateFormData => ({
  template_id: template.template_id.toString(),
  name: template.name,
  subject: template.subject,
  content: template.content,
  variables: Array.isArray(template.variables) 
    ? template.variables.reduce((acc, variable) => {
        acc[variable] = ''; // Initialize with empty values for form
        return acc;
      }, {} as Record<string, string>)
    : template.variables || {},
  is_active: template.is_active
});

const convertFormDataToCreateRequest = (formData: TemplateFormData): TemplateCreateRequest => ({
  template_id: formData.template_id,
  name: formData.name,
  subject: formData.subject,
  content: formData.content,
  variables: formData.variables,
  is_active: formData.is_active
});

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
  const [success, setSuccess] = useState<string | null>(null);
  const [isSendDialogOpen, setIsSendDialogOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationSummary[]>([]);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [sesQuota, setSesQuota] = useState<SESStatus>({
    max_24_hour: 0,
    max_send_rate: 0,
    sent_last_24_hours: 0,
    send_data_points: []
  });
  const navigate = useNavigate();
  
  // Fixed: Use proper form data structure
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateFormData>({
    template_id: '',
    name: '',
    subject: '',
    content: '',
    variables: {},
    is_active: true,
  });
  
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isTestDialogOpen, setIsTestDialogOpen] = useState(false);

  // Clear alerts after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching stats...');
      
      const [statsData, templatesData] = await Promise.all([
        apiService.getStats(),
        apiService.getTemplates(),
      ]);
      
      console.log('Stats data received:', statsData);
      setStats(statsData);
      setTemplates(templatesData);
      setNotifications(statsData.recent_notifications);
      if (statsData.ses_quota) {
        setSesQuota(statsData.ses_quota);
      }
      setError(null);
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
      setError('Failed to fetch dashboard data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleEditTemplate = (template: EmailTemplate) => {
    const formData = convertTemplateToFormData(template);
    setSelectedTemplate(formData);
    setIsEditDialogOpen(true);
  };

  // Fixed: Handle template ID as string
  const handleDeleteTemplate = async (templateId: string | number) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await apiService.deleteTemplate(templateId.toString());
        setSuccess('Template deleted successfully');
        fetchData();
      } catch (err) {
        console.error('Error deleting template:', err);
        setError('Failed to delete template');
      }
    }
  };

  const handleTestTemplate = (template: EmailTemplate) => {
    const formData = convertTemplateToFormData(template);
    setSelectedTemplate(formData);
    setIsTestDialogOpen(true);
  };

  const handleSaveTemplate = async () => {
    try {
      const createData = convertFormDataToCreateRequest(selectedTemplate);
      
      if (selectedTemplate.template_id) {
        // Update existing template
        await apiService.updateTemplate(selectedTemplate.template_id, createData);
        setSuccess('Template updated successfully');
      } else {
        // Create new template
        await apiService.addTemplate(createData);
        setSuccess('Template created successfully');
      }
      
      setIsEditDialogOpen(false);
      fetchData();
      
      // Reset form
      setSelectedTemplate({
        template_id: '',
        name: '',
        subject: '',
        content: '',
        variables: {},
        is_active: true,
      });
    } catch (error) {
      console.error('Error saving template:', error);
      setError('Failed to save template');
    }
  };

  const handleNewTemplate = () => {
    setSelectedTemplate({
      template_id: '',
      name: '',
      subject: '',
      content: '',
      variables: {},
      is_active: true,
    });
    setIsEditDialogOpen(true);
  };

  // Handle adding new variable
  const addVariable = () => {
    const newKey = `variable_${Object.keys(selectedTemplate.variables).length + 1}`;
    setSelectedTemplate({
      ...selectedTemplate,
      variables: {
        ...selectedTemplate.variables,
        [newKey]: ''
      }
    });
  };

  // Handle removing variable
  const removeVariable = (key: string) => {
    const newVariables = { ...selectedTemplate.variables };
    delete newVariables[key];
    setSelectedTemplate({
      ...selectedTemplate,
      variables: newVariables
    });
  };

  // Handle variable key/value changes
  const updateVariable = (oldKey: string, newKey: string, value: string) => {
    const newVariables = { ...selectedTemplate.variables };
    if (oldKey !== newKey) {
      delete newVariables[oldKey];
    }
    newVariables[newKey] = value;
    setSelectedTemplate({
      ...selectedTemplate,
      variables: newVariables
    });
  };

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
  }> = ({ title, value, icon, color = 'primary', filter, subtitle }) => (
    <Card 
      sx={{ 
        cursor: filter ? 'pointer' : 'default',
        '&:hover': filter ? { 
          transform: 'translateY(-2px)',
          boxShadow: 3,
          transition: 'all 0.2s ease-in-out'
        } : {},
        height: '100%',
        background: `linear-gradient(135deg, ${color}.light 0%, ${color}.main 100%)`,
        color: 'white',
      }}
      onClick={() => filter && handleStatCardClick(filter)}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
              {value}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5 }}>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box sx={{ 
            bgcolor: 'rgba(255,255,255,0.2)', 
            width: 48, 
            height: 48, 
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

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
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Email notification statistics
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={fetchData} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={() => setIsSendDialogOpen(true)}
            sx={{ borderRadius: 2 }}
          >
            Send Email
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {/* Debug Info */}
      <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Debug: Total: {stats.total_notifications}, Success: {stats.success_count}, Failed: {stats.failed_count}, Pending: {stats.pending_count}
        </Typography>
      </Box>

      {/* Email Count Stats */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Emails"
            value={stats.total_notifications || 0}
            icon={<EmailIcon />}
            color="primary"
            filter="all"
            subtitle="All time"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Successful"
            value={stats.success_count || 0}
            icon={<SuccessIcon />}
            color="success"
            filter="success"
            subtitle="Delivered"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Failed"
            value={stats.failed_count || 0}
            icon={<ErrorIcon />}
            color="error"
            filter="failed"
            subtitle="Needs retry"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending"
            value={stats.pending_count || 0}
            icon={<ScheduleIcon />}
            color="warning"
            filter="pending"
            subtitle="In queue"
          />
        </Grid>
      </Grid>

      {/* Send Email Section */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Send Email
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Send notifications to your users
              </Typography>
            </Box>
            <Box display="flex" gap={2}>
              <Tooltip title="Refresh Data">
                <IconButton onClick={fetchData} color="primary">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Button
                variant="contained"
                startIcon={<SendIcon />}
                onClick={() => setIsSendDialogOpen(true)}
                sx={{ borderRadius: 2 }}
              >
                Send New Email
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

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