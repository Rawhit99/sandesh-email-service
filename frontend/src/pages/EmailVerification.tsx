import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  VerifiedUser as VerifiedUserIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

const EmailVerification: React.FC = () => {
  const [verifiedEmails, setVerifiedEmails] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newEmail, setNewEmail] = useState('');
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    fetchVerifiedEmails();
  }, []);

  const fetchVerifiedEmails = async () => {
    try {
      const response = await apiService.getVerifiedEmails();
      // Ensure we always have an array, even if the response is empty
      setVerifiedEmails(Array.isArray(response) ? response : []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch verified emails');
      console.error(err);
      setVerifiedEmails([]); // Reset to empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEmail = async () => {
    if (!newEmail) return;

    setVerifying(true);
    try {
      await apiService.verifyEmail(newEmail);
      setNewEmail('');
      fetchVerifiedEmails();
      setError(null);
    } catch (err) {
      setError('Failed to send verification email');
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  const handleDeleteEmail = async (email: string) => {
    if (window.confirm(`Are you sure you want to remove ${email} from verified emails?`)) {
      try {
        await apiService.deleteVerifiedEmail(email);
        fetchVerifiedEmails();
      } catch (err) {
        setError('Failed to remove verified email');
        console.error(err);
      }
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Email Verification
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Verify New Email
          </Typography>
          <Box display="flex" gap={2}>
            <TextField
              label="Email Address"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              type="email"
              fullWidth
            />
            <Button
              variant="contained"
              color="primary"
              startIcon={<VerifiedUserIcon />}
              onClick={handleVerifyEmail}
              disabled={!newEmail || verifying}
            >
              {verifying ? 'Verifying...' : 'Verify Email'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Verified Emails
          </Typography>
          {verifiedEmails.length === 0 ? (
            <Typography color="text.secondary">
              No verified emails found. Add your first email address above.
            </Typography>
          ) : (
            <List>
              {verifiedEmails.map((email) => (
                <ListItem key={email}>
                  <ListItemText
                    primary={email}
                    secondary="Verified"
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => handleDeleteEmail(email)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default EmailVerification; 