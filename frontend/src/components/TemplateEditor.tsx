import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Grid,
  Typography,
  Card,
  CardContent,
  Alert,
  Chip,
  IconButton,
  FormControlLabel,
  Switch,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Stack,
  Divider,
} from '@mui/material';
import {
  Save as SaveIcon,
  Preview as PreviewIcon,
  Code as CodeIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  Email as EmailIcon,
  Subject as SubjectIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { EmailTemplate, TemplateFormData } from '../services/api';

interface TemplateEditorProps {
  initialData?: EmailTemplate;
  onSave: (data: TemplateFormData) => void;
  onCancel?: () => void;
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({
  initialData,
  onSave,
  onCancel,
}) => {
  const [formData, setFormData] = useState<TemplateFormData>({
    template_id: '',
    name: '',
    subject: '',
    content: '',
    variables: {},
    is_active: true,
  });
  const [showPreview, setShowPreview] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState<'desktop' | 'mobile'>('desktop');

  useEffect(() => {
    if (initialData) {
      setFormData({
        template_id: initialData.template_id,
        name: initialData.name,
        subject: initialData.subject,
        content: initialData.content,
        variables: initialData.variables || {},
        is_active: initialData.is_active,
      });
    }
  }, [initialData]);

  const extractVariables = (content: string): string[] => {
    const regex = /\{\{\s*(\w+)\s*\}\}/g;
    const variables = new Set<string>();
    let match;
    
    while ((match = regex.exec(content)) !== null) {
      variables.add(match[1]);
    }
    
    return Array.from(variables);
  };

  const handleContentChange = (content: string) => {
    setFormData(prev => ({ ...prev, content }));
    const variables = extractVariables(content);
    const variablesObj = variables.reduce((acc, var_name) => {
      acc[var_name] = formData.variables[var_name] || '';
      return acc;
    }, {} as Record<string, string>);
    
    setFormData(prev => ({ ...prev, variables: variablesObj }));
  };

  const handleVariableChange = (variable: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      variables: {
        ...prev.variables,
        [variable]: value,
      },
    }));
  };

  const handleAddVariable = () => {
    const newVar = `variable_${Object.keys(formData.variables).length + 1}`;
    setFormData(prev => ({
      ...prev,
      variables: {
        ...prev.variables,
        [newVar]: '',
      },
    }));
  };

  const handleRemoveVariable = (variable: string) => {
    setFormData(prev => {
      const newVariables = { ...prev.variables };
      delete newVariables[variable];
      return { ...prev, variables: newVariables };
    });
  };

  const handlePreview = () => {
    let preview = formData.content;
    Object.entries(formData.variables).forEach(([key, value]) => {
      const regex = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'g');
      preview = preview.replace(regex, value || `{{${key}}}`);
    });
    setPreviewContent(preview);
    setShowPreview(true);
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setValidationErrors([]);

    try {
      // Basic validation
      if (!formData.template_id.trim()) {
        setValidationErrors(['Template ID is required']);
        return;
      }
      if (!formData.name.trim()) {
        setValidationErrors(['Template name is required']);
        return;
      }
      if (!formData.subject.trim()) {
        setValidationErrors(['Subject is required']);
        return;
      }
      if (!formData.content.trim()) {
        setValidationErrors(['Content is required']);
        return;
      }

      await onSave(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save template');
    } finally {
      setLoading(false);
    }
  };

  const variables = Object.keys(formData.variables);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" component="h2" sx={{ fontWeight: 700 }}>
          {initialData ? 'Edit Template' : 'Create New Template'}
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<PreviewIcon />}
            onClick={handlePreview}
          >
            Preview
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? 'Saving…' : 'Save Template'}
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {validationErrors.length > 0 && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      <Grid container spacing={2}>
        {/* Left Column - Form */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined" sx={{ height: 'fit-content' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <EditIcon />
                Template Details
              </Typography>
              
              <TextField
                fullWidth
                label="Template ID"
                value={formData.template_id}
                onChange={(e) => setFormData(prev => ({ ...prev, template_id: e.target.value }))}
                margin="normal"
                required
                disabled={!!initialData}
                helperText={initialData ? "Template ID cannot be changed" : "Unique identifier for this template (letters, numbers, hyphens, underscores only)"}
              />
              
              <TextField
                fullWidth
                label="Template Name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                margin="normal"
                required
              />
              
              <TextField
                fullWidth
                label="Subject"
                value={formData.subject}
                onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                margin="normal"
                required
                InputProps={{
                  startAdornment: <SubjectIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                  />
                }
                label="Active Template"
                sx={{ mt: 2 }}
              />
            </CardContent>
          </Card>

          {/* Variables Section */}
          <Card variant="outlined" sx={{ mt: 2 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CodeIcon />
                  Template Variables
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={handleAddVariable}
                  variant="outlined"
                >
                  Add Variable
                </Button>
              </Box>
              
              {variables.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Typography color="text.secondary">
                    No variables found. Add variables using {'{{variable_name}}'} syntax in the content.
                  </Typography>
                </Box>
              ) : (
                <List dense>
                  {variables.map((variable) => (
                    <ListItem key={variable} sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip label={`{{${variable}}}`} size="small" color="primary" />
                            <Typography variant="body2" color="text.secondary">
                              {variable}
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <TextField
                          size="small"
                          placeholder="Default value"
                          value={formData.variables[variable] || ''}
                          onChange={(e) => handleVariableChange(variable, e.target.value)}
                          sx={{ width: 150 }}
                        />
                        <IconButton
                          size="small"
                          onClick={() => handleRemoveVariable(variable)}
                          sx={{ ml: 1 }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column - Content Editor */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined" sx={{ height: 'fit-content' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <EmailIcon />
                Email Content
              </Typography>
              
              <TextField
                fullWidth
                label="HTML Content"
                value={formData.content}
                onChange={(e) => handleContentChange(e.target.value)}
                multiline
                rows={15}
                margin="normal"
                required
                helperText="Use {{variable_name}} syntax for dynamic content"
                sx={{
                  '& .MuiInputBase-root': {
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                  },
                }}
              />
              <Divider sx={{ mt: 1.5, mb: 1 }} />
              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Chip size="small" variant="outlined" label={`${variables.length} variables`} />
                <Chip size="small" variant="outlined" label={formData.is_active ? 'Active template' : 'Inactive template'} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Enhanced Preview Dialog */}
      <Dialog
        open={showPreview}
        onClose={() => setShowPreview(false)}
        maxWidth="lg"
        fullWidth
        scroll="paper"
        PaperProps={{
          sx: {
            height: '90vh',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        <DialogTitle sx={{ pb: 1, flexShrink: 0 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Email Preview</Typography>
            <Box display="flex" gap={1}>
              <Button
                size="small"
                variant={previewMode === 'desktop' ? 'contained' : 'outlined'}
                onClick={() => setPreviewMode('desktop')}
              >
                Desktop
              </Button>
              <Button
                size="small"
                variant={previewMode === 'mobile' ? 'contained' : 'outlined'}
                onClick={() => setPreviewMode('mobile')}
              >
                Mobile
              </Button>
              <IconButton onClick={() => setShowPreview(false)}>
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent
          dividers
          sx={{
            p: 0,
            flex: '1 1 auto',
            minHeight: 0,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Box
            sx={{
              flex: '1 1 auto',
              minHeight: 0,
              display: 'flex',
              flexDirection: 'column',
              bgcolor: 'grey.100',
            }}
          >
            {/* Preview Header */}
            <Box
              sx={{
                flexShrink: 0,
                p: 2,
                bgcolor: 'white',
                borderBottom: 1,
                borderColor: 'grey.300',
              }}
            >
              <Typography variant="subtitle2" color="text.secondary">
                Subject: {formData.subject}
              </Typography>
            </Box>

            {/* Preview Content — scrollable (matches grid preview behavior) */}
            <Box
              sx={{
                flex: '1 1 auto',
                minHeight: 0,
                overflow: 'auto',
                p: 2,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'flex-start',
              }}
            >
              <Box
                sx={{
                  width: previewMode === 'mobile' ? 375 : 600,
                  maxWidth: '100%',
                  bgcolor: 'white',
                  borderRadius: 1.5,
                  boxShadow: 3,
                  overflow: 'auto',
                  maxHeight: '100%',
                }}
              >
                <Box
                  component="div"
                  sx={{ p: 2.5 }}
                  dangerouslySetInnerHTML={{ __html: previewContent }}
                />
              </Box>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default TemplateEditor;
