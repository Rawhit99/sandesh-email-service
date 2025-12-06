import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
  IconButton,
  Paper,
  Divider,
  Alert,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, Send as SendIcon, Preview as PreviewIcon } from '@mui/icons-material';
import apiService, { EmailTemplate, TemplateCreate, TemplateCreateRequest } from '../services/api';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

export interface Template {
  template_id: string;
  name: string;
  subject: string;
  content: string;
  created_at: string;
  updated_at: string;
  is_active: string;
}

interface TestPayload {
  email: string;
  payload: Record<string, any>;
}

const TemplateManagement: React.FC = () => {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [isTestDialogOpen, setIsTestDialogOpen] = useState(false);
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false);
  const [testPayload, setTestPayload] = useState<TestPayload>({
    email: '',
    payload: {},
  });
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [formData, setFormData] = useState<TemplateCreateRequest>({
    template_id: '',
    name: '',
    subject: '',
    content: '',
    variables: {},
    is_active: true,
  });

  const modules = {
    toolbar: [
      [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'color': [] }, { 'background': [] }],
      ['link', 'image'],
      ['clean']
    ],
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const data = await apiService.getTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setError('Failed to fetch templates');
    }
  };

  const handleCreateTemplate = async () => {
    try {
      await apiService.addTemplate(formData);
      setIsEditorOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Error creating template:', error);
      setError('Failed to create template');
    }
  };

  const handleEditTemplate = (template: EmailTemplate) => {
    const templateData: TemplateCreateRequest = {
      template_id: template.template_id,
      name: template.name,
      subject: template.subject,
      content: template.content,
      variables: template.variables,
      is_active: template.is_active,
    };
    setSelectedTemplate(template);
    setFormData(templateData);
    setIsEditorOpen(true);
  };

  const handleUpdateTemplate = async () => {
    if (!selectedTemplate) return;
    
    try {
      const updatedTemplate: TemplateCreate = {
        template_id: selectedTemplate.template_id,
        name: selectedTemplate.name,
        subject: selectedTemplate.subject,
        content: selectedTemplate.content,
        variables: selectedTemplate.variables,
        is_active: selectedTemplate.is_active,
      };
      await apiService.updateTemplate(selectedTemplate.template_id, updatedTemplate);
      setIsEditorOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Error updating template:', error);
      setError('Failed to update template');
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await apiService.deleteTemplate(templateId);
        fetchTemplates();
        setSuccess('Template deleted successfully');
      } catch (error) {
        console.error('Error deleting template:', error);
        setError('Failed to delete template');
      }
    }
  };

  const handleSaveTemplate = async (templateData: TemplateCreateRequest) => {
    try {
      if (selectedTemplate) {
        await apiService.updateTemplate(selectedTemplate.template_id, templateData);
      } else {
        await apiService.addTemplate(templateData);
      }
      setIsEditorOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Error saving template:', error);
      setError('Failed to save template');
    }
  };

  const handleTestTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template);
    setTestPayload({
      email: '',
      payload: {},
    });
    setIsTestDialogOpen(true);
  };

  const handlePreviewTemplate = (template: EmailTemplate) => {
    setSelectedTemplate(template);
    generatePreview(template);
    setIsPreviewDialogOpen(true);
  };

  const generatePreview = (template: EmailTemplate) => {
    try {
      // Replace template variables with sample data
      let previewContent = template.content;
      const sampleData = {
        user_name: 'John Doe',
        account_id: 'ACC123',
        user_email: 'john@example.com',
        company_name: 'Acme Corp',
        registration_date: new Date().toLocaleDateString(),
        // Add more sample data as needed
      };

      // Replace variables in the format {{variable_name}}
      Object.entries(sampleData).forEach(([key, value]) => {
        const regex = new RegExp(`{{${key}}}`, 'g');
        previewContent = previewContent.replace(regex, value.toString());
      });

      setPreviewHtml(previewContent);
    } catch (error) {
      console.error('Error generating preview:', error);
      setError('Failed to generate preview');
    }
  };

  const handleSendTest = async () => {
    if (!selectedTemplate) return;

    try {
      await apiService.sendEmail({
        template_id: selectedTemplate.template_id,
        email: testPayload.email,
        payload: testPayload.payload,
      });
      setIsTestDialogOpen(false);
      setSuccess('Test email sent successfully!');
    } catch (error) {
      console.error('Error sending test email:', error);
      setError('Failed to send test email');
    }
  };

  const handlePayloadChange = (key: string, value: string) => {
    setTestPayload(prev => ({
      ...prev,
      payload: {
        ...prev.payload,
        [key]: value,
      },
    }));
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Email Templates</Typography>
        <Button variant="contained" color="primary" onClick={() => {
          setSelectedTemplate(null);
          setFormData({
            template_id: '',
            name: '',
            subject: '',
            content: '',
            variables: {},
            is_active: true,
          });
          setIsEditorOpen(true);
        }}>
          Create Template
        </Button>
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

      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.template_id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {template.name}
                </Typography>
                <Typography variant="subtitle1" color="textSecondary" gutterBottom>
                  {template.subject}
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  ID: {template.template_id}
                </Typography>
                <Box mt={2} display="flex" gap={1}>
                  <IconButton
                    size="small"
                    onClick={() => handleEditTemplate(template)}
                    title="Edit"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteTemplate(template.template_id)}
                    title="Delete"
                  >
                    <DeleteIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleTestTemplate(template)}
                    title="Test"
                  >
                    <SendIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handlePreviewTemplate(template)}
                    title="Preview"
                  >
                    <PreviewIcon />
                  </IconButton>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Edit Template Dialog */}
      <Dialog open={isEditorOpen} onClose={() => setIsEditorOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedTemplate?.template_id ? 'Edit Template' : 'Create Template'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Template ID"
                fullWidth
                value={selectedTemplate?.template_id || formData.template_id}
                onChange={(e) => {
                  if (selectedTemplate) {
                    setSelectedTemplate(prev => prev ? { ...prev, template_id: e.target.value } : null);
                  } else {
                    setFormData(prev => ({ ...prev, template_id: e.target.value }));
                  }
                }}
                disabled={!!selectedTemplate}
                helperText={selectedTemplate ? "Template ID cannot be changed" : "Unique identifier for this template"}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Name"
                fullWidth
                value={selectedTemplate?.name || formData.name}
                onChange={(e) => {
                  if (selectedTemplate) {
                    setSelectedTemplate(prev => prev ? { ...prev, name: e.target.value } : null);
                  } else {
                    setFormData(prev => ({ ...prev, name: e.target.value }));
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Subject"
                fullWidth
                value={selectedTemplate?.subject || formData.subject}
                onChange={(e) => {
                  if (selectedTemplate) {
                    setSelectedTemplate(prev => prev ? { ...prev, subject: e.target.value } : null);
                  } else {
                    setFormData(prev => ({ ...prev, subject: e.target.value }));
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Content
              </Typography>
              <ReactQuill
                theme="snow"
                value={selectedTemplate?.content || formData.content}
                onChange={(content: string) => {
                  if (selectedTemplate) {
                    setSelectedTemplate(prev => prev ? { ...prev, content } : null);
                  } else {
                    setFormData(prev => ({ ...prev, content }));
                  }
                }}
                modules={modules}
                style={{ height: '200px', marginBottom: '50px' }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsEditorOpen(false)}>Cancel</Button>
          <Button onClick={() => selectedTemplate ? handleUpdateTemplate() : handleCreateTemplate()} variant="contained" color="primary">
            {selectedTemplate ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Template Dialog */}
      <Dialog open={isTestDialogOpen} onClose={() => setIsTestDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Test Template</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Test Email"
                fullWidth
                type="email"
                value={testPayload.email}
                onChange={(e) => setTestPayload(prev => ({ ...prev, email: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Payload Variables
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {Object.keys(testPayload.payload).map((key) => (
                <TextField
                  key={key}
                  label={key}
                  fullWidth
                  value={testPayload.payload[key]}
                  onChange={(e) => handlePayloadChange(key, e.target.value)}
                  sx={{ mb: 2 }}
                />
              ))}
              <Button
                variant="outlined"
                onClick={() => {
                  const newKey = prompt('Enter variable name:');
                  if (newKey) {
                    handlePayloadChange(newKey, '');
                  }
                }}
              >
                Add Variable
              </Button>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsTestDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSendTest} variant="contained" color="primary">
            Send Test
          </Button>
        </DialogActions>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={isPreviewDialogOpen} onClose={() => setIsPreviewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Template Preview</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              {selectedTemplate?.subject}
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box
              sx={{
                p: 2,
                border: '1px solid #ddd',
                borderRadius: 1,
                backgroundColor: '#f9f9f9',
              }}
            >
              <div dangerouslySetInnerHTML={{ __html: previewHtml || "" }} />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsPreviewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TemplateManagement; 