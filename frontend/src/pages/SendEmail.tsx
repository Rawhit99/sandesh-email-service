import React, { useState, useEffect, ChangeEvent } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
  Alert,
  CircularProgress,
  SelectChangeEvent,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import apiService, { EmailRequest, EmailTemplate } from '../services/api';

// Define the expected payload structure
interface EmailPayload {
  user_name: string;
  account_id: string;
  user_email: string;
  company_name: string;
  registration_date: string;
}

const SendEmail = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state with structured payload
  const [formData, setFormData] = useState<{
    template_id: string;
    email: string;
    cc_emails: string;
    payload: EmailPayload;
  }>({
    template_id: '',
    email: '',
    cc_emails: '',
    payload: {
      user_name: '',
      account_id: '',
      user_email: '',
      company_name: '',
      registration_date: '',
    },
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const templatesList = await apiService.getTemplates();
      console.log('Templates loaded:', templatesList);
      setTemplates(templatesList);
    } catch (err) {
      console.error('Error loading templates:', err);
      setError('Failed to load email templates');
    }
  };

  const handleInputChange = (field: string) => (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
  };

  const handlePayloadChange = (field: keyof EmailPayload) => (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      payload: {
        ...formData.payload,
        [field]: event.target.value,
      },
    });
  };

  const handleSelectChange = (event: SelectChangeEvent) => {
    setFormData({
      ...formData,
      template_id: event.target.value,
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Prepare request
      const request: EmailRequest = {
        template_id: formData.template_id,
        email: formData.email,
        payload: formData.payload,
        ...(formData.cc_emails && {
          cc_emails: formData.cc_emails.split(',').map(email => email.trim()),
        }),
      };

      console.log('Sending request:', request);

      // Send email
      const response = await apiService.sendEmail(request);
      setSuccess(`Email sent successfully! Message ID: ${response.message_id}`);
      
      // Reset form
      setFormData({
        template_id: '',
        email: '',
        cc_emails: '',
        payload: {
          user_name: '',
          account_id: '',
          user_email: '',
          company_name: '',
          registration_date: '',
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Send New Email
      </Typography>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Email Template</InputLabel>
            <Select
              value={formData.template_id}
              label="Email Template"
              onChange={handleSelectChange}
              required
            >
              {templates.map((template) => (
                <MenuItem key={template.template_id} value={template.template_id}>
                  {template.subject}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Recipient Email"
            type="email"
            value={formData.email}
            onChange={handleInputChange('email')}
            required
            sx={{ mb: 3 }}
          />

          <TextField
            fullWidth
            label="CC Emails (comma-separated)"
            value={formData.cc_emails}
            onChange={handleInputChange('cc_emails')}
            helperText="Optional: Enter multiple email addresses separated by commas"
            sx={{ mb: 3 }}
          />

          <Typography variant="h6" sx={{ mb: 2 }}>
            Template Variables
          </Typography>

          <TextField
            fullWidth
            label="User Name"
            value={formData.payload.user_name}
            onChange={handlePayloadChange('user_name')}
            required
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Account ID"
            value={formData.payload.account_id}
            onChange={handlePayloadChange('account_id')}
            required
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="User Email"
            type="email"
            value={formData.payload.user_email}
            onChange={handlePayloadChange('user_email')}
            required
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Company Name"
            value={formData.payload.company_name}
            onChange={handlePayloadChange('company_name')}
            required
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Registration Date"
            type="date"
            value={formData.payload.registration_date}
            onChange={handlePayloadChange('registration_date')}
            required
            InputLabelProps={{ shrink: true }}
            sx={{ mb: 3 }}
          />

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              sx={{ minWidth: 120 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Send Email'}
            </Button>
            <Button
              variant="outlined"
              onClick={() => navigate('/templates')}
            >
              View Templates
            </Button>
          </Box>
        </form>
      </Paper>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SendEmail;