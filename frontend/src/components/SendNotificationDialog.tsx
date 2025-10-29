import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Box,
  Alert,
} from '@mui/material';
import apiService, { EmailTemplate } from '../services/api';

interface SendNotificationDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const SendNotificationDialog: React.FC<SendNotificationDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [customContent, setCustomContent] = useState<string>('');
  const [useCustomContent, setUseCustomContent] = useState<boolean>(false);
  const [formData, setFormData] = useState({
    email: '',
    subject: '',
    content: '',
    cc_emails: '',
    payload: {} as Record<string, any>,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [templateVariables, setTemplateVariables] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      fetchTemplates();
    }
  }, [open]);

  const fetchTemplates = async () => {
    try {
      const data = await apiService.getTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setError('Failed to fetch templates');
    }
  };

  const extractTemplateVariables = (content: string) => {
    const regex = /{{([^}]+)}}/g;
    const variables = new Set<string>();
    let match;
    while ((match = regex.exec(content)) !== null) {
      variables.add(match[1].trim());
    }
    return Array.from(variables);
  };

  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplate(templateId);
    const template = templates.find(t => t.template_id === templateId);
    if (template) {
      setFormData(prev => ({
        ...prev,
        subject: template.subject,
        content: template.content,
      }));
      // Extract variables from template content
      const variables = extractTemplateVariables(template.content);
      setTemplateVariables(variables);
      
      // Initialize payload with empty values for all variables
      const initialPayload = variables.reduce((acc, variable) => ({
        ...acc,
        [variable]: '',
      }), {});
      setFormData(prev => ({
        ...prev,
        payload: initialPayload,
      }));
    }
  };

  const handleCustomContentChange = (content: string) => {
    setFormData(prev => ({ ...prev, content }));
    const variables = extractTemplateVariables(content);
    setTemplateVariables(variables);
    
    // Update payload to include new variables
    const updatedPayload = { ...formData.payload };
    variables.forEach(variable => {
      if (!(variable in updatedPayload)) {
        updatedPayload[variable] = '';
      }
    });
    setFormData(prev => ({
      ...prev,
      payload: updatedPayload,
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    // Ensure payload is not empty
    if (!formData.payload || Object.values(formData.payload).every(val => !val)) {
      setError("Please fill at least one variable for the template.");
      setLoading(false);
      return;
    }

    try {
      const request = {
        template_id: useCustomContent ? 'custom' : selectedTemplate,
        email: formData.email,
        cc_emails: formData.cc_emails ? formData.cc_emails.split(',').map(email => email.trim()) : undefined,
        payload: formData.payload,
        ...(useCustomContent && {
          subject: formData.subject,
          content: formData.content,
        }),
      };

      await apiService.sendEmail(request);
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error sending notification:', error);
      setError('Failed to send notification');
    } finally {
      setLoading(false);
    }
  };

  const handlePayloadChange = (key: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      payload: {
        ...prev.payload,
        [key]: value,
      },
    }));
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Send New Notification</DialogTitle>
      <DialogContent>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Use Template</InputLabel>
              <Select
                value={useCustomContent ? 'custom' : 'template'}
                onChange={(e) => setUseCustomContent(e.target.value === 'custom')}
              >
                <MenuItem value="template">Use Existing Template</MenuItem>
                <MenuItem value="custom">Custom Content</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {!useCustomContent && (
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Select Template</InputLabel>
                <Select
                  value={selectedTemplate}
                  onChange={(e) => handleTemplateChange(e.target.value)}
                >
                  {templates.map((template) => (
                    <MenuItem key={template.template_id} value={template.template_id}>
                      {template.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}

          <Grid item xs={12}>
            <TextField
              label="Recipient Email"
              fullWidth
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="CC Emails (comma-separated)"
              fullWidth
              value={formData.cc_emails}
              onChange={(e) => setFormData(prev => ({ ...prev, cc_emails: e.target.value }))}
              helperText="Multiple emails can be added, separated by commas"
            />
          </Grid>

          {useCustomContent && (
            <>
              <Grid item xs={12}>
                <TextField
                  label="Subject"
                  fullWidth
                  value={formData.subject}
                  onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Content"
                  fullWidth
                  multiline
                  rows={6}
                  value={formData.content}
                  onChange={(e) => handleCustomContentChange(e.target.value)}
                  required
                  helperText="Use {{variable_name}} for dynamic content"
                />
              </Grid>
            </>
          )}

          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Template Variables
            </Typography>
            <Box sx={{ mb: 2 }}>
              {templateVariables.map((variable) => (
                <TextField
                  key={variable}
                  label={variable}
                  fullWidth
                  value={formData.payload[variable] || ''}
                  onChange={(e) => handlePayloadChange(variable, e.target.value)}
                  sx={{ mb: 2 }}
                  required
                  helperText={`Value for {{${variable}}}`}
                />
              ))}
              {templateVariables.length === 0 && (
                <Typography color="textSecondary">
                  No variables found in the template
                </Typography>
              )}
            </Box>
          </Grid>

          {error && (
            <Grid item xs={12}>
              <Alert severity="error">{error}</Alert>
            </Grid>
          )}
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={loading || !formData.email || (!useCustomContent && !selectedTemplate)}
        >
          {loading ? 'Sending...' : 'Send Notification'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SendNotificationDialog;
