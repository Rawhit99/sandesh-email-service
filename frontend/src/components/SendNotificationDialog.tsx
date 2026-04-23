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
  Stack,
  Chip,
  Divider,
} from '@mui/material';
import apiService, { EmailRequest, EmailTemplate } from '../services/api';

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
  const [useCustomContent, setUseCustomContent] = useState<boolean>(false);
  const [formData, setFormData] = useState({
    email: '',
    subject: '',
    content: '',
    cc_emails: '',
    from_email: '',
    sender_name: '',
    payload: {} as Record<string, any>,
  });
  const [channels, setChannels] = useState<string[]>(['email']);
  const [attachmentName, setAttachmentName] = useState('');
  const [attachmentB64, setAttachmentB64] = useState('');
  const [attachmentMime, setAttachmentMime] = useState('application/octet-stream');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [templateVariables, setTemplateVariables] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      void fetchTemplates();
      setAttachmentName('');
      setAttachmentB64('');
      setAttachmentMime('application/octet-stream');
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

    const hasAttachment = Boolean(attachmentB64);
    const hasPayloadValues =
      formData.payload &&
      Object.values(formData.payload).some(val => val != null && String(val).trim() !== '');
    if (templateVariables.length > 0 && !hasPayloadValues && !hasAttachment) {
      setError('Fill at least one template variable, or attach a file.');
      setLoading(false);
      return;
    }
    if (useCustomContent && (!formData.subject.trim() || !formData.content.trim())) {
      setError('Subject and HTML content are required for custom content.');
      setLoading(false);
      return;
    }

    try {
      const trimmedFrom = formData.from_email.trim();
      const trimmedSender = formData.sender_name.trim();
      const request: EmailRequest = {
        template_id: useCustomContent ? 'custom' : selectedTemplate,
        email: formData.email,
        cc_emails: formData.cc_emails ? formData.cc_emails.split(',').map(email => email.trim()) : undefined,
        payload: formData.payload || {},
        ...(useCustomContent && {
          subject: formData.subject,
          content: formData.content,
        }),
        ...(trimmedFrom ? { from_email: trimmedFrom } : {}),
        ...(trimmedSender ? { sender_name: trimmedSender } : {}),
        ...(channels.length ? { channels } : {}),
        ...(hasAttachment
          ? {
              attachments: [
                {
                  filename: attachmentName || 'attachment',
                  content_base64: attachmentB64,
                  mime_type: attachmentMime || 'application/octet-stream',
                },
              ],
            }
          : {}),
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
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Send Notification</Typography>
          <Chip size="small" variant="outlined" label={useCustomContent ? 'Custom content' : 'Template'} />
        </Stack>
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={1.5} sx={{ mt: 0.5 }}>
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
            <Divider sx={{ my: 0.5 }} />
          </Grid>

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

          <Grid item xs={12} md={6}>
            <TextField
              label="From email (override)"
              fullWidth
              type="email"
              value={formData.from_email}
              onChange={(e) => setFormData((prev) => ({ ...prev, from_email: e.target.value }))}
              helperText="Optional; must be allowed by your provider"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              label="Sender display name"
              fullWidth
              value={formData.sender_name}
              onChange={(e) => setFormData((prev) => ({ ...prev, sender_name: e.target.value }))}
            />
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>Channels</InputLabel>
              <Select
                multiple
                label="Channels"
                value={channels}
                onChange={(e) => setChannels(typeof e.target.value === 'string' ? [e.target.value] : e.target.value)}
                renderValue={(selected) => (selected as string[]).join(', ')}
              >
                {['email', 'slack', 'ms_teams', 'whatsapp', 'push_fcm', 'push_sns'].map((c) => (
                  <MenuItem key={c} value={c}>
                    {c}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
              Non-email channels run after a successful email. Configure webhooks in backend .env (Integrations page).
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Button variant="outlined" component="label" size="small">
              Attach file (optional)
              <input
                type="file"
                hidden
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  setAttachmentName(f.name);
                  setAttachmentMime(f.type && f.type.length > 0 ? f.type : 'application/octet-stream');
                  const reader = new FileReader();
                  reader.onload = () => {
                    const r = reader.result as string;
                    const b64 = r.includes(',') ? r.split(',')[1] : r;
                    setAttachmentB64(b64 || '');
                  };
                  reader.readAsDataURL(f);
                }}
              />
            </Button>
            {attachmentName && (
              <Typography variant="caption" sx={{ ml: 2 }}>
                {attachmentName}
              </Typography>
            )}
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
            <Divider sx={{ my: 0.5 }} />
          </Grid>

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
        <Button variant="outlined" onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color="primary"
          disabled={loading || !formData.email || (!useCustomContent && !selectedTemplate)}
        >
          {loading ? 'Sending…' : 'Send Notification'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SendNotificationDialog;
