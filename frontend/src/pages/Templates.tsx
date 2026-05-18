import React, { useEffect, useState } from 'react';
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
  Stack,
  Tabs,
  Tab,
  Tooltip,
  TextField,
  Typography,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Close as CloseIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Preview as PreviewIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import apiService, { EmailTemplate, TemplateFormData } from '../services/api';
import TemplateEditor from '../components/TemplateEditor';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);

  const getContentPreview = (content: string): string => {
    const doc = new DOMParser().parseFromString(content, 'text/html');
    const textOnly = doc.body.textContent ?? '';
    return textOnly.substring(0, 120);
  };
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  const totalVariables = templates.reduce((acc, t) => acc + Object.keys(t.variables || {}).length, 0);
  const activeTemplates   = templates.filter(t => t.is_active);
  const inactiveTemplates = templates.filter(t => !t.is_active);
  const currentTemplates  = activeTab === 0 ? activeTemplates : inactiveTemplates;
  const filteredTemplates = currentTemplates.filter((t) => {
    const q = searchTerm.trim().toLowerCase();
    if (!q) return true;
    return (
      t.template_id.toLowerCase().includes(q) ||
      t.name.toLowerCase().includes(q) ||
      t.subject.toLowerCase().includes(q) ||
      String(t.content || '').toLowerCase().includes(q)
    );
  });

  const fetchTemplates = async (background = false) => {
    try {
      background ? setRefreshing(true) : setLoading(true);
      setError(null);
      const data = await apiService.getTemplates();
      setTemplates(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
    } finally {
      background ? setRefreshing(false) : setLoading(false);
    }
  };

  useEffect(() => { void fetchTemplates(); }, []);

  const handleSaveTemplate = async (templateData: TemplateFormData) => {
    try {
      if (selectedTemplate) {
        await apiService.updateTemplate(selectedTemplate.template_id, templateData);
        setSuccess('Template updated successfully');
      } else {
        await apiService.addTemplate(templateData);
        setSuccess('Template created successfully');
      }
      setIsEditorOpen(false);
      setSelectedTemplate(null);
      void fetchTemplates(true);
    } catch {
      setError('Failed to save template');
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    if (!window.confirm('Delete this template? This cannot be undone.')) return;
    try {
      await apiService.deleteTemplate(templateId);
      setSuccess('Template deleted');
      void fetchTemplates(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete template');
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'template_id', headerName: 'Template ID', width: 160,
      renderCell: (p) => <Typography variant="body2" sx={{ fontWeight: 600, fontFamily: 'monospace', color: 'primary.main' }}>{p.value}</Typography>,
    },
    {
      field: 'name', headerName: 'Name', width: 180,
      renderCell: (p) => <Typography variant="body2" sx={{ fontWeight: 500 }}>{p.value}</Typography>,
    },
    {
      field: 'subject', headerName: 'Subject', width: 240,
      renderCell: (p) => <Typography variant="body2" noWrap>{p.value}</Typography>,
    },
    {
      field: 'content', headerName: 'Content preview', flex: 1, minWidth: 200,
      renderCell: (p) => (
        <Typography variant="body2" color="text.secondary" noWrap>
          {getContentPreview(String(p.value ?? ''))}
        </Typography>
      ),
    },
    {
      field: 'variables', headerName: 'Variables', width: 110,
      renderCell: (p) => (
        <Chip label={`${Object.keys(p.value || {}).length} vars`} size="small" variant="outlined" />
      ),
    },
    {
      field: 'is_active', headerName: 'Status', width: 100,
      renderCell: (p) => (
        <Chip label={p.value ? 'Active' : 'Inactive'} size="small" variant="outlined" color={p.value ? 'success' : 'default'} />
      ),
    },
    {
      field: 'created_at', headerName: 'Created', width: 120,
      renderCell: (p) => <Typography variant="body2" color="text.secondary">{new Date(p.value).toLocaleDateString()}</Typography>,
    },
    {
      field: 'actions', headerName: 'Actions', width: 130, sortable: false,
      renderCell: (p) => (
        <Stack direction="row" spacing={0.5}>
          <Tooltip title="Preview">
            <IconButton size="small" onClick={() => { setPreviewContent(p.row.content); setIsPreviewOpen(true); }}>
              <PreviewIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit">
            <IconButton size="small" color="primary" onClick={() => { setSelectedTemplate(p.row); setIsEditorOpen(true); }}>
              <EditIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" color="error" onClick={() => void handleDeleteTemplate(p.row.template_id)}>
              <DeleteIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
        </Stack>
      ),
    },
  ];

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
          Console › Templates
        </Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4">Email templates</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              Create and manage reusable email templates with dynamic variables
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexShrink={0}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon sx={{ fontSize: 15 }} />}
              onClick={() => void fetchTemplates(true)}
              disabled={refreshing}
              size="small"
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon sx={{ fontSize: 15 }} />}
              onClick={() => { setSelectedTemplate(null); setIsEditorOpen(true); }}
              size="small"
            >
              Create template
            </Button>
          </Stack>
        </Stack>
        <Box sx={{ mt: 1.5 }}>
          <TextField
            size="small"
            placeholder="Search by template id, name, subject, content..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ width: { xs: '100%', md: 420 } }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 0.75, fontSize: 16, color: 'text.secondary' }} />,
            }}
          />
        </Box>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip size="small" variant="outlined" label={`${templates.length} total`} />
          <Chip size="small" variant="outlined" label={`${activeTemplates.length} active`} color="success" />
          {inactiveTemplates.length > 0 && (
            <Chip size="small" variant="outlined" label={`${inactiveTemplates.length} inactive`} />
          )}
          <Chip size="small" variant="outlined" label={`${totalVariables} variables`} />
        </Stack>
      </Box>

      {refreshing && <LinearProgress />}

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

        {/* Main content panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
          {/* Tabs */}
          <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
            <Tab
              label={
                <Stack direction="row" spacing={1} alignItems="center">
                  <VisibilityIcon sx={{ fontSize: 14 }} />
                  <span>Active</span>
                  <Chip label={activeTemplates.length} size="small" variant="outlined" />
                </Stack>
              }
            />
            <Tab
              label={
                <Stack direction="row" spacing={1} alignItems="center">
                  <VisibilityOffIcon sx={{ fontSize: 14 }} />
                  <span>Inactive</span>
                  <Chip label={inactiveTemplates.length} size="small" variant="outlined" />
                </Stack>
              }
            />
          </Tabs>

          {/* Table / empty */}
          {filteredTemplates.length === 0 ? (
            <Box sx={{ py: 8, textAlign: 'center' }}>
              <VisibilityOffIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1.5, opacity: 0.5 }} />
              <Typography variant="h6" color="text.secondary">
                No {activeTab === 0 ? 'active' : 'inactive'} templates
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {activeTab === 0 ? 'Create your first template to get started' : 'All templates are currently active'}
              </Typography>
              {activeTab === 0 && (
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => { setSelectedTemplate(null); setIsEditorOpen(true); }}
                  sx={{ mt: 2 }}
                  size="small"
                >
                  Create template
                </Button>
              )}
            </Box>
          ) : (
            <DataGrid
              rows={filteredTemplates}
              columns={columns}
              getRowId={(r) => r.template_id}
              pageSizeOptions={[10, 25, 50]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              disableRowSelectionOnClick
              autoHeight
              sx={{
                border: 'none',
                borderRadius: 0,
                '& .MuiDataGrid-columnHeaders': {
                  backgroundColor: 'background.paper',
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: 'text.primary',
                },
                '& .MuiDataGrid-cell': {
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  fontSize: '0.8125rem',
                },
                '& .MuiDataGrid-row:hover': { backgroundColor: 'action.hover' },
                '& .MuiDataGrid-footerContainer': {
                  borderTop: '1px solid',
                  borderColor: 'divider',
                  backgroundColor: 'background.paper',
                },
              }}
            />
          )}
        </Box>
      </Box>

      {/* ── Editor dialog ──────────────────────────────────────────── */}
      <Dialog open={isEditorOpen} onClose={() => setIsEditorOpen(false)} maxWidth="xl" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{selectedTemplate ? 'Edit template' : 'Create template'}</span>
          <IconButton size="small" onClick={() => setIsEditorOpen(false)}>
            <CloseIcon sx={{ fontSize: 18 }} />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TemplateEditor
              initialData={selectedTemplate || undefined}
              onSave={handleSaveTemplate}
              onCancel={() => setIsEditorOpen(false)}
            />
          </Box>
        </DialogContent>
      </Dialog>

      {/* ── Preview dialog ──────────────────────────────────────────── */}
      <Dialog open={isPreviewOpen} onClose={() => setIsPreviewOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Template preview</span>
          <IconButton size="small" onClick={() => setIsPreviewOpen(false)}><CloseIcon sx={{ fontSize: 18 }} /></IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
            <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 3 }}>
              <div dangerouslySetInnerHTML={{ __html: previewContent }} />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" size="small" onClick={() => setIsPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Templates;
