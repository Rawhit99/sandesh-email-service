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
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Tabs,
  Tab,
} from '@mui/material';
import apiService from '../services/api';

interface SESSettings {
  aws_access_key_id: string;
  aws_secret_access_key: string;
  aws_region: string;
  ses_sender_email: string;
  ses_configuration_set?: string;
}

interface SMTPSettings {
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  smtp_sender_email: string;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
}

interface EmailSettings {
  email_provider: 'ses' | 'smtp';
  ses?: SESSettings;
  smtp?: SMTPSettings;
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [emailProvider, setEmailProvider] = useState<'ses' | 'smtp'>('ses');
  const [sesSettings, setSesSettings] = useState<SESSettings>({
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_region: '',
    ses_sender_email: '',
    ses_configuration_set: '',
  });
  const [smtpSettings, setSmtpSettings] = useState<SMTPSettings>({
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_sender_email: '',
    smtp_use_tls: true,
    smtp_use_ssl: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isTestDialogOpen, setIsTestDialogOpen] = useState(false);
  const [testSettings, setTestSettings] = useState<EmailSettings>({
    email_provider: 'ses',
    ses: {
      aws_access_key_id: '',
      aws_secret_access_key: '',
      aws_region: '',
      ses_sender_email: '',
      ses_configuration_set: '',
    },
    smtp: {
      smtp_host: '',
      smtp_port: 587,
      smtp_username: '',
      smtp_password: '',
      smtp_sender_email: '',
      smtp_use_tls: true,
      smtp_use_ssl: false,
    },
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await apiService.getEmailSettings();
      setEmailProvider(data.email_provider);
      
      if (data.email_provider === 'ses') {
        setSesSettings({
          aws_access_key_id: data.aws_access_key_id || '',
          aws_secret_access_key: data.aws_secret_access_key || '',
          aws_region: data.aws_region || '',
          ses_sender_email: data.ses_sender_email || '',
          ses_configuration_set: data.ses_configuration_set || '',
        });
      } else {
        setSmtpSettings({
          smtp_host: data.smtp_host || '',
          smtp_port: data.smtp_port || 587,
          smtp_username: data.smtp_username || '',
          smtp_password: data.smtp_password || '',
          smtp_sender_email: data.smtp_sender_email || '',
          smtp_use_tls: data.smtp_use_tls !== false,
          smtp_use_ssl: data.smtp_use_ssl === true,
        });
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
      setError('Failed to fetch settings');
    }
  };

  const handleSaveSettings = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const settings = {
        email_provider: emailProvider,
        ...(emailProvider === 'ses' ? sesSettings : smtpSettings),
      };
      
      await apiService.updateEmailSettings(settings);
      setSuccess('Settings updated successfully');
    } catch (error) {
      console.error('Error updating settings:', error);
      setError('Failed to update settings');
    } finally {
      setLoading(false);
    }
  };

  const handleTestSettings = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiService.testEmailSettings(testSettings);
      setSuccess('Test successful! Settings are valid.');
      setIsTestDialogOpen(false);
    } catch (error) {
      console.error('Error testing settings:', error);
      setError('Test failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleProviderChange = (provider: 'ses' | 'smtp') => {
    setEmailProvider(provider);
  };

  return (
    <Box>
      <Typography variant="h4" mb={3}>Settings</Typography>
      
      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>Email Provider Configuration</Typography>
          
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Email Provider</InputLabel>
            <Select
              value={emailProvider}
              onChange={(e) => handleProviderChange(e.target.value as 'ses' | 'smtp')}
            >
              <MenuItem value="ses">AWS SES</MenuItem>
              <MenuItem value="smtp">SMTP</MenuItem>
            </Select>
          </FormControl>

          {emailProvider === 'ses' ? (
            <Box component="form">
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="AWS Access Key ID"
                    fullWidth
                    value={sesSettings.aws_access_key_id}
                    onChange={e => setSesSettings({ ...sesSettings, aws_access_key_id: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="AWS Secret Access Key"
                    fullWidth
                    type="password"
                    value={sesSettings.aws_secret_access_key}
                    onChange={e => setSesSettings({ ...sesSettings, aws_secret_access_key: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="AWS Region"
                    fullWidth
                    value={sesSettings.aws_region}
                    onChange={e => setSesSettings({ ...sesSettings, aws_region: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="SES Sender Email"
                    fullWidth
                    value={sesSettings.ses_sender_email}
                    onChange={e => setSesSettings({ ...sesSettings, ses_sender_email: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="SES Configuration Set"
                    fullWidth
                    value={sesSettings.ses_configuration_set}
                    onChange={e => setSesSettings({ ...sesSettings, ses_configuration_set: e.target.value })}
                  />
                </Grid>
              </Grid>
            </Box>
          ) : (
            <Box component="form">
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="SMTP Host"
                    fullWidth
                    value={smtpSettings.smtp_host}
                    onChange={e => setSmtpSettings({ ...smtpSettings, smtp_host: e.target.value })}
                    placeholder="smtp.gmail.com"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="SMTP Port"
                    fullWidth
                    type="number"
                    value={smtpSettings.smtp_port}
                    onChange={e => setSmtpSettings({ ...smtpSettings, smtp_port: parseInt(e.target.value) })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="SMTP Username"
                    fullWidth
                    value={smtpSettings.smtp_username}
                    onChange={e => setSmtpSettings({ ...smtpSettings, smtp_username: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="SMTP Password"
                    fullWidth
                    type="password"
                    value={smtpSettings.smtp_password}
                    onChange={e => setSmtpSettings({ ...smtpSettings, smtp_password: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Sender Email"
                    fullWidth
                    value={smtpSettings.smtp_sender_email}
                    onChange={e => setSmtpSettings({ ...smtpSettings, smtp_sender_email: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={smtpSettings.smtp_use_tls}
                        onChange={(e) => setSmtpSettings({ ...smtpSettings, smtp_use_tls: e.target.checked })}
                      />
                    }
                    label="Use TLS"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={smtpSettings.smtp_use_ssl}
                        onChange={(e) => setSmtpSettings({ ...smtpSettings, smtp_use_ssl: e.target.checked })}
                      />
                    }
                    label="Use SSL"
                  />
                </Grid>
              </Grid>
            </Box>
          )}
          
          <Box mt={3}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSaveSettings}
              disabled={loading}
              sx={{ mr: 2 }}
            >
              Save Settings
            </Button>
            <Button
              variant="outlined"
              onClick={() => setIsTestDialogOpen(true)}
              disabled={loading}
            >
              Test Settings
            </Button>
          </Box>
          
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
        </CardContent>
      </Card>

      {/* Test Settings Dialog */}
      <Dialog open={isTestDialogOpen} onClose={() => setIsTestDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Test Email Settings</DialogTitle>
        <DialogContent>
          <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 2 }}>
            <Tab label="SES" />
            <Tab label="SMTP" />
          </Tabs>
          
          {activeTab === 0 && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="AWS Access Key ID"
                  fullWidth
                  value={testSettings.ses?.aws_access_key_id || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    ses: { ...testSettings.ses!, aws_access_key_id: e.target.value }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="AWS Secret Access Key"
                  fullWidth
                  type="password"
                  value={testSettings.ses?.aws_secret_access_key || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    ses: { ...testSettings.ses!, aws_secret_access_key: e.target.value }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="AWS Region"
                  fullWidth
                  value={testSettings.ses?.aws_region || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    ses: { ...testSettings.ses!, aws_region: e.target.value }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="SES Sender Email"
                  fullWidth
                  value={testSettings.ses?.ses_sender_email || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    ses: { ...testSettings.ses!, ses_sender_email: e.target.value }
                  })}
                />
              </Grid>
            </Grid>
          )}
          
          {activeTab === 1 && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="SMTP Host"
                  fullWidth
                  value={testSettings.smtp?.smtp_host || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    smtp: { ...testSettings.smtp!, smtp_host: e.target.value }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="SMTP Port"
                  fullWidth
                  type="number"
                  value={testSettings.smtp?.smtp_port || 587}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    smtp: { ...testSettings.smtp!, smtp_port: parseInt(e.target.value) }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="SMTP Username"
                  fullWidth
                  value={testSettings.smtp?.smtp_username || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    smtp: { ...testSettings.smtp!, smtp_username: e.target.value }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="SMTP Password"
                  fullWidth
                  type="password"
                  value={testSettings.smtp?.smtp_password || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    smtp: { ...testSettings.smtp!, smtp_password: e.target.value }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Sender Email"
                  fullWidth
                  value={testSettings.smtp?.smtp_sender_email || ''}
                  onChange={e => setTestSettings({
                    ...testSettings,
                    smtp: { ...testSettings.smtp!, smtp_sender_email: e.target.value }
                  })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={testSettings.smtp?.smtp_use_tls || false}
                      onChange={(e) => setTestSettings({
                        ...testSettings,
                        smtp: { ...testSettings.smtp!, smtp_use_tls: e.target.checked }
                      })}
                    />
                  }
                  label="Use TLS"
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsTestDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleTestSettings} variant="contained" disabled={loading}>
            {loading ? 'Testing...' : 'Test Settings'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings; 