/**
 * Credentials page – manage multiple named credential profiles per channel.
 *
 * Users can:
 *   1. Create multiple profiles per channel (e.g. "prod-ses", "staging-ses")
 *   2. Set one profile as the default for that channel
 *   3. Reference a non-default profile when sending: pass `credential_name` in the notification payload
 */

import React, { useCallback, useEffect, useState } from 'react';
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
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Key as KeyIcon,
  Refresh as RefreshIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
} from '@mui/icons-material';
import apiService, { IntegrationCredential } from '../services/api';

/* ── channel metadata ─────────────────────────────────────────────────────── */

export interface ChannelDef {
  id: string;
  label: string;
  description: string;
  fields: { key: string; label: string; secret?: boolean; placeholder?: string }[];
}

export const CHANNELS: ChannelDef[] = [
  {
    id: 'aws_ses',
    label: 'AWS SES',
    description: 'Simple Email Service — transactional email delivery',
    fields: [
      { key: 'aws_access_key_id',     label: 'Access Key ID',     placeholder: 'AKIA…' },
      { key: 'aws_secret_access_key', label: 'Secret Access Key', secret: true },
      { key: 'aws_session_token',     label: 'Session Token (optional, STS)', secret: true },
      { key: 'aws_region',            label: 'Region',            placeholder: 'us-east-1' },
      { key: 'ses_sender_email',      label: 'Sender Email',      placeholder: 'no-reply@example.com' },
    ],
  },
  {
    id: 'sns',
    label: 'Amazon SNS',
    description: 'Simple Notification Service — push / SMS delivery',
    fields: [
      { key: 'aws_access_key_id',     label: 'Access Key ID',     placeholder: 'AKIA…' },
      { key: 'aws_secret_access_key', label: 'Secret Access Key', secret: true },
      { key: 'aws_session_token',     label: 'Session Token (optional, STS)', secret: true },
      { key: 'aws_region',            label: 'Region',            placeholder: 'ap-south-1' },
      { key: 'sns_push_topic_arn',    label: 'Topic ARN',         placeholder: 'arn:aws:sns:ap-south-1:123456789012:my-topic' },
    ],
  },
  {
    id: 'smtp',
    label: 'SMTP',
    description: 'Relay email through any mail server',
    fields: [
      { key: 'smtp_host',     label: 'SMTP Host',     placeholder: 'smtp.example.com' },
      { key: 'smtp_port',     label: 'Port',          placeholder: '587' },
      { key: 'smtp_username', label: 'Username' },
      { key: 'smtp_password', label: 'Password',      secret: true },
      { key: 'smtp_from',     label: 'From address',  placeholder: 'no-reply@example.com' },
    ],
  },
  {
    id: 'slack',
    label: 'Slack',
    description: 'Incoming webhook notifications to Slack channels',
    fields: [
      { key: 'webhook_url', label: 'Incoming Webhook URL', placeholder: 'https://hooks.slack.com/services/…' },
    ],
  },
  {
    id: 'ms_teams',
    label: 'Microsoft Teams',
    description: 'Workflows & connectors webhook',
    fields: [
      { key: 'webhook_url', label: 'Webhook URL', placeholder: 'https://…powerautomate.com/…' },
    ],
  },
  {
    id: 'firebase',
    label: 'Firebase (FCM)',
    description: 'Cloud Messaging — mobile push notifications',
    fields: [
      { key: 'credentials_path', label: 'Service account JSON path', placeholder: '/etc/secrets/firebase.json' },
    ],
  },
  {
    id: 'twilio_whatsapp',
    label: 'WhatsApp (Twilio)',
    description: 'Outbound WhatsApp messages via Twilio',
    fields: [
      { key: 'account_sid', label: 'Account SID', placeholder: 'ACxxxxxxxx' },
      { key: 'auth_token',  label: 'Auth Token',  secret: true },
      { key: 'from',        label: 'From number', placeholder: 'whatsapp:+14155238886' },
    ],
  },
];

export const channelMap = Object.fromEntries(CHANNELS.map(c => [c.id, c]));

/* ── credential form dialog ──────────────────────────────────────────────── */

interface CredDialogProps {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  initial?: IntegrationCredential | null;  // null = create
  fixedChannel?: string;
}

export function CredentialDialog({ open, onClose, onSaved, initial, fixedChannel }: CredDialogProps) {
  const isEdit = Boolean(initial);
  const [channel, setChannel] = useState(fixedChannel || initial?.channel || CHANNELS[0].id);
  const [name, setName] = useState(initial?.name || '');
  const [isDefault, setIsDefault] = useState(initial?.is_default ?? false);
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const channelDef = channelMap[channel];

  // populate config on open
  useEffect(() => {
    if (open) {
      setChannel(fixedChannel || initial?.channel || CHANNELS[0].id);
      setName(initial?.name || '');
      setIsDefault(initial?.is_default ?? false);
      const vals: Record<string, string> = {};
      if (initial?.config) {
        for (const [k, v] of Object.entries(initial.config)) {
          vals[k] = String(v);
        }
      }
      setConfigValues(vals);
      setErr(null);
    }
  }, [open, initial, fixedChannel]);

  const setField = (key: string, val: string) =>
    setConfigValues(prev => ({ ...prev, [key]: val }));

  const handleSave = async () => {
    setErr(null);
    if (!name.trim()) { setErr('Credential name is required'); return; }
    const config: Record<string, string> = {};
    for (const [k, v] of Object.entries(configValues)) {
      if (v.trim()) config[k] = v.trim();
    }
    setSaving(true);
    try {
      if (isEdit && initial) {
        await apiService.updateCredential(initial.id, { name: name.trim(), config, is_default: isDefault });
      } else {
        await apiService.createCredential({ channel, name: name.trim(), config, is_default: isDefault });
      }
      onSaved();
      onClose();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEdit ? 'Edit credential' : 'Add credential'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 0.5 }}>
          {!fixedChannel && !isEdit && (
            <Select
              value={channel}
              onChange={e => setChannel(e.target.value)}
              size="small"
              fullWidth
            >
              {CHANNELS.map(c => (
                <MenuItem key={c.id} value={c.id}>{c.label}</MenuItem>
              ))}
            </Select>
          )}
          {(fixedChannel || isEdit) && (
            <Box sx={{ bgcolor: 'action.hover', borderRadius: 1, px: 1.5, py: 1 }}>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>{channelDef?.label}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>{channelDef?.description}</Typography>
            </Box>
          )}

          <TextField
            label="Credential name / identifier"
            value={name}
            onChange={e => setName(e.target.value)}
            size="small"
            fullWidth
            placeholder="e.g. production, staging, client-a"
            helperText="Pass this name as credential_name in the notification payload to use this profile"
          />

          <Divider />

          {channelDef?.fields.map(f => (
            <TextField
              key={f.key}
              label={f.label}
              value={configValues[f.key] || ''}
              onChange={e => setField(f.key, e.target.value)}
              size="small"
              fullWidth
              type={f.secret ? 'password' : 'text'}
              placeholder={f.secret ? '(unchanged if left blank)' : f.placeholder}
              autoComplete={f.secret ? 'new-password' : undefined}
            />
          ))}

          <FormControlLabel
            control={<Switch checked={isDefault} onChange={e => setIsDefault(e.target.checked)} size="small" />}
            label={<Typography variant="body2">Set as default for this channel</Typography>}
          />

          {err && <Alert severity="error">{err}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button variant="outlined" size="small" onClick={onClose}>Cancel</Button>
        <Button variant="contained" size="small" disabled={saving} onClick={() => void handleSave()}>
          {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add credential'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

/* ── main page ───────────────────────────────────────────────────────────── */

const CredentialsPage: React.FC = () => {
  const [creds, setCreds] = useState<IntegrationCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editCred, setEditCred] = useState<IntegrationCredential | null>(null);
  const [addChannel, setAddChannel] = useState<string | undefined>(undefined);

  const load = useCallback(async (bg = false) => {
    bg ? setRefreshing(true) : setLoading(true);
    setError(null);
    try {
      const data = await apiService.listCredentials();
      setCreds(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load credentials');
    } finally {
      bg ? setRefreshing(false) : setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleSetDefault = async (id: number) => {
    try {
      await apiService.setDefaultCredential(id);
      await load(true);
      setSuccess('Default credential updated');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to set default');
    }
  };

  const handleDelete = async (id: number, credName: string) => {
    if (!window.confirm(`Delete credential "${credName}"? This cannot be undone.`)) return;
    try {
      await apiService.deleteCredential(id);
      await load(true);
      setSuccess('Credential deleted');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Delete failed');
    }
  };

  // Group by channel
  const byChannel = CHANNELS.map(ch => ({
    def: ch,
    items: creds.filter(c => c.channel === ch.id),
  })).filter(g => g.items.length > 0);

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
          Console › Integrations › Credentials
        </Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4">Credential profiles</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              Store multiple named credential sets per channel. Pass <code>credential_name</code> in the notification payload to use a non-default profile.
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} flexShrink={0}>
            <Button variant="outlined" startIcon={<RefreshIcon sx={{ fontSize: 15 }} />} size="small"
              onClick={() => void load(true)} disabled={refreshing}>
              Refresh
            </Button>
            <Button variant="contained" startIcon={<AddIcon sx={{ fontSize: 15 }} />} size="small"
              onClick={() => { setEditCred(null); setAddChannel(undefined); setDialogOpen(true); }}>
              Add credential
            </Button>
          </Stack>
        </Stack>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip size="small" variant="outlined" label={`${creds.length} total`} />
          <Chip size="small" variant="outlined" label={`${byChannel.length} channels`} color="primary" />
          <Chip size="small" variant="outlined" label={`${creds.filter(c => c.is_default).length} defaults set`} color="success" />
        </Stack>
      </Box>

      {refreshing && <LinearProgress />}

      {/* ── How to use info box ──────────────────────────────────── */}
      <Box sx={{ bgcolor: 'background.default', px: { xs: 2, md: 3 }, pt: 2 }}>
        <Alert
          severity="info"
          icon={false}
          sx={{ mb: 2, '& .MuiAlert-message': { width: '100%' } }}
        >
          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>How to use a non-default credential</Typography>
          <Typography variant="body2" color="text.secondary">
            When sending a notification, include <code>credential_name</code> in your payload to select a specific profile:
          </Typography>
          <Box component="pre" sx={{ mt: 1, mb: 0, p: 1.5, bgcolor: 'background.default', border: '1px solid', borderColor: 'divider', borderRadius: 1, fontSize: '0.75rem', fontFamily: 'monospace', overflowX: 'auto' }}>
{`POST /api/v1/notifications/send
{
  "template_id": "welcome",
  "email": "user@example.com",
  "payload": {
    "name": "Alice",
    "credential_name": "staging-ses"   // ← references the named credential
  }
}`}
          </Box>
        </Alert>
      </Box>

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ px: { xs: 2, md: 3 }, pb: 3 }}>
        {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

        {creds.length === 0 ? (
          <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, py: 8, textAlign: 'center' }}>
            <KeyIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1.5, opacity: 0.4 }} />
            <Typography variant="h6" color="text.secondary">No credentials yet</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 2 }}>
              Add credential profiles to use multiple accounts per channel
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              size="small"
              onClick={() => { setEditCred(null); setAddChannel(undefined); setDialogOpen(true); }}
            >
              Add credential
            </Button>
          </Box>
        ) : (
          <Stack spacing={2}>
            {byChannel.map(({ def, items }) => (
              <Box key={def.id} sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
                {/* Channel header */}
                <Box sx={{ px: 2.5, py: 1.5, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: 'background.default' }}>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>{def.label}</Typography>
                    <Typography variant="caption" color="text.secondary">{def.description}</Typography>
                  </Box>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<AddIcon sx={{ fontSize: 13 }} />}
                    onClick={() => { setEditCred(null); setAddChannel(def.id); setDialogOpen(true); }}
                  >
                    Add profile
                  </Button>
                </Box>

                {/* Credentials table */}
                <TableContainer component={Paper} sx={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Profile name</TableCell>
                        <TableCell>Config keys</TableCell>
                        <TableCell>Default</TableCell>
                        <TableCell>Created</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {items.map(cred => (
                        <TableRow key={cred.id} hover>
                          <TableCell>
                            <Box component="code" sx={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: 'primary.main', bgcolor: 'action.hover', px: 0.75, py: 0.25, borderRadius: 0.5 }}>
                              {cred.name}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={0.5} flexWrap="wrap">
                              {Object.keys(cred.config).map(k => (
                                <Chip key={k} size="small" label={k} variant="outlined" sx={{ height: 18, fontSize: '0.7rem' }} />
                              ))}
                              {Object.keys(cred.config).length === 0 && (
                                <Typography variant="caption" color="text.secondary">—</Typography>
                              )}
                            </Stack>
                          </TableCell>
                          <TableCell>
                            {cred.is_default ? (
                              <Chip size="small" label="Default" color="success" variant="outlined" icon={<StarIcon sx={{ fontSize: '12px !important' }} />} />
                            ) : (
                              <Typography variant="caption" color="text.secondary">—</Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {new Date(cred.created_at).toLocaleDateString()}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                              {!cred.is_default && (
                                <Tooltip title="Set as default">
                                  <IconButton size="small" onClick={() => void handleSetDefault(cred.id)}>
                                    <StarBorderIcon sx={{ fontSize: 16 }} />
                                  </IconButton>
                                </Tooltip>
                              )}
                              <Tooltip title="Edit">
                                <IconButton size="small" color="primary" onClick={() => { setEditCred(cred); setAddChannel(undefined); setDialogOpen(true); }}>
                                  <EditIcon sx={{ fontSize: 16 }} />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete">
                                <IconButton size="small" color="error" onClick={() => void handleDelete(cred.id, cred.name)}>
                                  <DeleteIcon sx={{ fontSize: 16 }} />
                                </IconButton>
                              </Tooltip>
                            </Stack>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            ))}
          </Stack>
        )}
      </Box>

      {/* ── Credential dialog ─────────────────────────────────────── */}
      <CredentialDialog
        open={dialogOpen}
        onClose={() => { setDialogOpen(false); setEditCred(null); }}
        onSaved={() => void load(true)}
        initial={editCred}
        fixedChannel={addChannel}
      />
    </Box>
  );
};

export default CredentialsPage;
