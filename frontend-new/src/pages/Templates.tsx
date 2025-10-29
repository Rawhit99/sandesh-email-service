import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  IconButton,
  Tabs,
  Tab,
  Paper,
  Divider,
  Tooltip,
  Grid,
  Chip,
  Avatar,
  LinearProgress,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Preview as PreviewIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Code as CodeIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import apiService, { EmailTemplate, TemplateCreate, TemplateValidationRequest, TemplateFormData } from '../services/api';
import TemplateEditor from '../components/TemplateEditor';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getTemplates();
      setTemplates(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setSelectedTemplate(null);
    setIsEditorOpen(true);
  };

  const handleEditTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template);
    setIsEditorOpen(true);
  };

  const handlePreviewTemplate = (template: EmailTemplate) => {
    setPreviewContent(template.content);
    setIsPreviewOpen(true);
  };

  const handleSaveTemplate = async (templateData: TemplateFormData) => {
    try {
      setError(null);
      setSuccess(null);

      if (selectedTemplate) {
        await apiService.updateTemplate(selectedTemplate.template_id, templateData);
        setSuccess('Template updated successfully');
      } else {
        await apiService.addTemplate(templateData);
        setSuccess('Template created successfully');
      }

      setIsEditorOpen(false);
      setSelectedTemplate(null);
      fetchTemplates();
    } catch (error) {
      console.error('Error saving template:', error);
      setError('Failed to save template');
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await apiService.deleteTemplate(templateId);
        setSuccess('Template deleted successfully');
        fetchTemplates();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete template');
        console.error(err);
      }
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const columns: GridColDef[] = [
    { 
      field: 'template_id', 
      headerName: 'Template ID', 
      width: 150,
      renderCell: (params) => (
        <Box display="flex" alignItems="center">
          <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: 'primary.main' }}>
            {params.value.charAt(0).toUpperCase()}
          </Avatar>
          <Typography variant="body2" fontWeight="medium">
            {params.value}
          </Typography>
        </Box>
      )
    },
    { 
      field: 'name', 
      headerName: 'Name', 
      width: 200,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="medium">
          {params.value}
        </Typography>
      )
    },
    { 
      field: 'subject', 
      headerName: 'Subject', 
      width: 250,
      renderCell: (params) => (
        <Typography variant="body2" noWrap>
          {params.value}
        </Typography>
      )
    },
    {
      field: 'content',
      headerName: 'Content Preview',
      width: 300,
      renderCell: (params) => {
        const content = params.value as string;
        const preview = content.replace(/<[^>]*>/g, '').substring(0, 100);
        return (
          <Typography variant="body2" color="text.secondary" noWrap>
            {preview}...
          </Typography>
        );
      },
    },
    {
      field: 'variables',
      headerName: 'Variables',
      width: 150,
      renderCell: (params) => {
        const variables = params.value as Record<string, string>;
        const count = Object.keys(variables || {}).length;
        return (
          <Chip 
            label={`${count} vars`} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        );
      },
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          size="small"
          color={params.value ? 'success' : 'default'}
          variant="filled"
        />
      ),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 180,
      renderCell: (params) => (
        <Typography variant="body2" color="text.secondary">
          {new Date(params.value).toLocaleDateString()}
        </Typography>
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 200,
      sortable: false,
      renderCell: (params) => (
        <Box display="flex" gap={1}>
          <Tooltip title="Preview Template">
            <IconButton
              size="small"
              onClick={() => handlePreviewTemplate(params.row)}
              color="primary"
            >
              <PreviewIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit Template">
            <IconButton
              size="small"
              onClick={() => handleEditTemplate(params.row)}
              color="primary"
            >
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete Template">
            <IconButton
              size="small"
              onClick={() => handleDeleteTemplate(params.row.template_id)}
              color="error"
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  // Filter templates based on active tab
  const activeTemplates = templates.filter(t => t.is_active);
  const inactiveTemplates = templates.filter(t => !t.is_active);
  const currentTemplates = activeTab === 0 ? activeTemplates : inactiveTemplates;

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            Email Templates
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Create and manage your email templates
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchTemplates} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateTemplate}
            sx={{ borderRadius: 2 }}
          >
            Create Template
          </Button>
        </Box>
      </Box>

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

      {/* Stats Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CodeIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                    {templates.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Templates
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <VisibilityIcon sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                    {activeTemplates.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Templates
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <VisibilityOffIcon sx={{ fontSize: 40, color: 'warning.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                    {inactiveTemplates.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Inactive Templates
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <CodeIcon sx={{ fontSize: 40, color: 'info.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                    {templates.reduce((acc, t) => acc + Object.keys(t.variables || {}).length, 0)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Variables
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Template Tabs */}
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
                  <VisibilityIcon fontSize="small" />
                  <Typography>Active Templates</Typography>
                  <Chip label={activeTemplates.length} size="small" color="success" />
                </Box>
              } 
            />
            <Tab 
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <VisibilityOffIcon fontSize="small" />
                  <Typography>Inactive Templates</Typography>
                  <Chip label={inactiveTemplates.length} size="small" color="warning" />
                </Box>
              } 
            />
          </Tabs>
        </CardContent>
      </Card>

      {/* Templates Table */}
      <Card>
        <CardContent>
          <Box sx={{ height: 600, width: '100%' }}>
            {currentTemplates.length === 0 ? (
              <Box 
                display="flex" 
                flexDirection="column" 
                alignItems="center" 
                justifyContent="center" 
                height="100%"
                py={4}
              >
                <VisibilityOffIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No {activeTab === 0 ? 'Active' : 'Inactive'} Templates
                </Typography>
                <Typography variant="body2" color="text.secondary" textAlign="center">
                  {activeTab === 0 
                    ? 'Create your first template to get started' 
                    : 'All templates are currently active'
                  }
                </Typography>
                {activeTab === 0 && (
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleCreateTemplate}
                    sx={{ mt: 2 }}
                  >
                    Create Template
                  </Button>
                )}
              </Box>
            ) : (
              <DataGrid
                rows={currentTemplates}
                columns={columns}
                pageSizeOptions={[10, 25, 50]}
                initialState={{
                  pagination: { paginationModel: { pageSize: 10 } },
                }}
                disableRowSelectionOnClick
                sx={{
                  '& .MuiDataGrid-cell:hover': {
                    backgroundColor: 'action.hover',
                  },
                  '& .MuiDataGrid-row:hover': {
                    backgroundColor: 'action.hover',
                  },
                }}
              />
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Template Editor Dialog */}
      <Dialog
        open={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        maxWidth="xl"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {selectedTemplate ? 'Edit Template' : 'Create New Template'}
            </Typography>
            <IconButton onClick={() => setIsEditorOpen(false)}>
              <DeleteIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ p: 2 }}>
            <TemplateEditor
              initialData={selectedTemplate || undefined}
              onSave={handleSaveTemplate}
              onCancel={() => setIsEditorOpen(false)}
            />
          </Box>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog
        open={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Typography variant="h6">Template Preview</Typography>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ minHeight: 400 }}>
            <div
              dangerouslySetInnerHTML={{ __html: previewContent }}
              style={{
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                padding: '20px',
                minHeight: '300px',
                backgroundColor: '#ffffff'
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Templates; 