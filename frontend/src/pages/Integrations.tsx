import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Avatar,
  Box,
  Button,
  CardActionArea,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import Add from '@mui/icons-material/Add';
import Close from '@mui/icons-material/Close';
import ContentCopy from '@mui/icons-material/ContentCopy';
import Delete from '@mui/icons-material/Delete';
import Edit from '@mui/icons-material/Edit';
import LockOutlined from '@mui/icons-material/LockOutlined';
import Star from '@mui/icons-material/Star';
import StarBorder from '@mui/icons-material/StarBorder';
import apiService, { IntegrationCredential, IntegrationMe, IntegrationStatus } from '../services/api';
import { CredentialDialog, channelMap } from './Credentials';

type StatusKey = keyof IntegrationStatus;

/**
 * Direct SVG URLs (SVGRepo: `https://www.svgrepo.com/svg/{id}/{slug}` → download `{slug}.svg`).
 * AWS SNS: [worldvectorlogo page](https://worldvectorlogo.com/logo/aws-sns) plus SVGRepo vector + local fallback.
 */
function localBrandSvgUrl(brandFile: string): string {
  const base = (process.env.PUBLIC_URL || '').replace(/\/$/, '');
  return `${base}/brands/${brandFile}.svg`;
}

const INTEGRATION_CARDS: {
  key: StatusKey;
  title: string;
  subtitle: string;
  envVar: string;
  /** Remote SVGs first; last resort is `iconLocalFile` → `/brands/*.svg` */
  iconUrls?: string[];
  iconLocalFile?: string;
  brandColor: string;
  letter: string;
  useLock?: boolean;
}[] = [
  {
    key: 'slack_incoming_webhook',
    title: 'Slack',
    subtitle: 'Incoming webhooks',
    envVar: 'SLACK_INCOMING_WEBHOOK_URL',
    // Page: https://www.svgrepo.com/svg/303320/slack-new-logo-logo — embed uses /show/…svg (download URLs often fail in <img>)
    iconUrls: [
      'https://www.svgrepo.com/show/303320/slack-new-logo-logo.svg',
      'https://www.svgrepo.com/download/303320/slack-new-logo-logo.svg',
      'https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg',
    ],
    iconLocalFile: 'slack',
    brandColor: '#4A154B',
    letter: 'S',
  },
  {
    key: 'ms_teams_incoming_webhook',
    title: 'Microsoft Teams',
    subtitle: 'Workflows & connectors',
    envVar: 'MS_TEAMS_INCOMING_WEBHOOK_URL',
    iconUrls: [
      'https://www.svgrepo.com/show/452111/teams.svg',
      'https://www.svgrepo.com/download/452111/teams.svg',
    ],
    iconLocalFile: 'microsoftteams',
    brandColor: '#6264A7',
    letter: 'T',
  },
  {
    key: 'email_ses',
    title: 'AWS SES',
    subtitle: 'Transactional email (Simple Email Service)',
    envVar: 'EMAIL_PROVIDER=ses · AWS_ACCESS_KEY_ID · SES_SENDER_EMAIL',
    iconUrls: [
      'https://www.svgrepo.com/show/353461/aws-ses.svg',
      'https://www.svgrepo.com/download/353461/aws-ses.svg',
    ],
    iconLocalFile: 'amazonaws',
    brandColor: '#232F3E',
    letter: 'E',
  },
  {
    key: 'email_smtp',
    title: 'SMTP',
    subtitle: 'Relay email through your mail server',
    envVar: 'EMAIL_PROVIDER=smtp · SMTP_HOST · SMTP_USERNAME',
    iconUrls: [
      'https://www.svgrepo.com/show/452051/email-smtp.svg',
      'https://www.svgrepo.com/download/452051/email-smtp.svg',
    ],
    brandColor: '#4f46e5',
    letter: 'M',
  },
  {
    key: 'firebase',
    title: 'Firebase',
    subtitle: 'Cloud Messaging (FCM)',
    envVar: 'FIREBASE_CREDENTIALS_PATH',
    iconUrls: [
      'https://www.svgrepo.com/show/373595/firebase.svg',
      'https://www.svgrepo.com/download/373595/firebase.svg',
    ],
    iconLocalFile: 'firebase',
    brandColor: '#FFCA28',
    letter: 'F',
  },
  {
    key: 'sns',
    title: 'Amazon SNS',
    subtitle: 'Mobile push',
    envVar: 'SNS_PUSH_TOPIC_ARN',
    iconUrls: [
      'https://cdn.worldvectorlogo.com/logos/aws-sns.svg',
      'https://www.svgrepo.com/download/353462/aws-sns.svg',
    ],
    iconLocalFile: 'amazonaws',
    brandColor: '#232F3E',
    letter: 'A',
  },
  {
    key: 'twilio_whatsapp',
    title: 'WhatsApp',
    subtitle: 'Outbound via Twilio',
    envVar: 'TWILIO_ACCOUNT_SID · TWILIO_AUTH_TOKEN · TWILIO_WHATSAPP_FROM',
    iconUrls: [
      'https://www.svgrepo.com/show/303147/whatsapp-icon-logo.svg',
      'https://www.svgrepo.com/download/303147/whatsapp-icon-logo.svg',
    ],
    iconLocalFile: 'whatsapp',
    brandColor: '#25D366',
    letter: 'W',
  },
  {
    key: 'redis_queue',
    title: 'Redis & RQ',
    subtitle: 'Async email queue',
    envVar: 'REDIS_URL · worker.py',
    iconUrls: [
      'https://www.svgrepo.com/show/303460/redis-logo.svg',
      'https://www.svgrepo.com/download/303460/redis-logo.svg',
    ],
    iconLocalFile: 'redis',
    brandColor: '#DC382D',
    letter: 'R',
  },
  {
    key: 'subscriber_required',
    title: 'Subscriber gate',
    subtitle: 'Require Novu-style subscriber on send',
    envVar: 'SUBSCRIBER_REQUIRED=true',
    brandColor: '#1565c0',
    letter: 'N',
    useLock: true,
  },
];

function integrationIconSrcList(iconUrls?: string[], iconLocalFile?: string): string[] {
  const list = [...(iconUrls ?? [])];
  if (iconLocalFile) {
    list.push(localBrandSvgUrl(iconLocalFile));
  }
  return list;
}

function IntegrationLogo(props: {
  iconUrls?: string[];
  iconLocalFile?: string;
  letter: string;
  brandColor: string;
  useLock?: boolean;
}) {
  const { iconUrls, iconLocalFile, letter, brandColor, useLock } = props;
  const urls = integrationIconSrcList(iconUrls, iconLocalFile);
  const [urlIndex, setUrlIndex] = useState(0);
  const urlKey = urls.join('|');

  useEffect(() => {
    setUrlIndex(0);
  }, [urlKey]);

  if (useLock) {
    return (
      <Avatar
        variant="rounded"
        sx={{
          width: 44,
          height: 44,
          bgcolor: 'background.default',
          color: 'text.secondary',
          border: '1px solid',
          borderColor: 'divider',
        }}
      >
        <LockOutlined sx={{ fontSize: 22 }} />
      </Avatar>
    );
  }

  const src = urls[urlIndex];
  const showImg = Boolean(src) && urlIndex < urls.length;

  return (
    <Box
      sx={{
        width: 44,
        height: 44,
        borderRadius: 1,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.paper',
        color: 'text.secondary',
        border: '1px solid',
        borderColor: 'divider',
        p: 0.5,
        boxSizing: 'border-box',
      }}
    >
      {showImg ? (
        <Box
          component="img"
          src={src}
          alt=""
          loading="lazy"
          onError={() => setUrlIndex((i) => i + 1)}
          sx={{
            width: '100%',
            height: '100%',
            maxWidth: 32,
            maxHeight: 32,
            objectFit: 'contain',
            display: 'block',
          }}
        />
      ) : (
        <Typography sx={{ fontWeight: 700, fontSize: '0.95rem' }}>{letter}</Typography>
      )}
    </Box>
  );
}

type EnvFieldDef = {
  apiKey: string;
  envCopyName: string;
  label: string;
  secret?: boolean;
  placeholder?: string;
};

const ENV_INTEGRATION_FIELDS: Partial<Record<StatusKey, EnvFieldDef[]>> = {
  firebase: [
    {
      apiKey: 'firebase_credentials_path',
      envCopyName: 'FIREBASE_CREDENTIALS_PATH',
      label: 'Service account JSON path (on server)',
      placeholder: '/etc/secrets/firebase-adminsdk.json',
    },
  ],
  sns: [
    {
      apiKey: 'sns_push_topic_arn',
      envCopyName: 'SNS_PUSH_TOPIC_ARN',
      label: 'SNS topic ARN',
      placeholder: 'arn:aws:sns:ap-south-1:123456789012:my-topic',
    },
    {
      apiKey: 'sns_access_key_id',
      envCopyName: 'AWS_ACCESS_KEY_ID',
      label: 'SNS AWS access key ID',
      placeholder: 'AKIA...',
    },
    {
      apiKey: 'sns_secret_access_key',
      envCopyName: 'AWS_SECRET_ACCESS_KEY',
      label: 'SNS AWS secret access key',
      secret: true,
      placeholder: 'Leave blank to use server/default credentials',
    },
    {
      apiKey: 'sns_session_token',
      envCopyName: 'AWS_SESSION_TOKEN',
      label: 'SNS AWS session token (optional)',
      secret: true,
      placeholder: 'Required for temporary STS credentials',
    },
    {
      apiKey: 'sns_region',
      envCopyName: 'AWS_REGION',
      label: 'SNS AWS region',
      placeholder: 'ap-south-1',
    },
  ],
  twilio_whatsapp: [
    { apiKey: 'twilio_account_sid', envCopyName: 'TWILIO_ACCOUNT_SID', label: 'Twilio Account SID', placeholder: 'ACxxxxxxxx' },
    { apiKey: 'twilio_auth_token', envCopyName: 'TWILIO_AUTH_TOKEN', label: 'Twilio Auth Token', secret: true },
    { apiKey: 'twilio_whatsapp_from', envCopyName: 'TWILIO_WHATSAPP_FROM', label: 'WhatsApp From', placeholder: 'whatsapp:+14155238886' },
  ],
  redis_queue: [
    { apiKey: 'redis_url', envCopyName: 'REDIS_URL', label: 'Redis URL (stored for reference; worker still uses server env)', placeholder: 'redis://localhost:6379/0' },
  ],
};

/** Maps integration card key → credential channel id (undefined = no named credentials for this channel) */
const CARD_CREDENTIAL_CHANNEL: Partial<Record<StatusKey, string>> = {
  slack_incoming_webhook:       'slack',
  ms_teams_incoming_webhook:    'ms_teams',
  email_ses:                    'aws_ses',
  email_smtp:                   'smtp',
  sns:                          'sns',
  firebase:                     'firebase',
  twilio_whatsapp:              'twilio_whatsapp',
};

/* ── Channel credentials section (embedded inside the configure dialog) ──── */

type ChannelCredentialsSectionProps = {
  channelId: string;
  credentials: IntegrationCredential[];
  onReload: () => Promise<void>;
};

function ChannelCredentialsSection({ channelId, credentials, onReload }: ChannelCredentialsSectionProps) {
  const [credDialogOpen, setCredDialogOpen] = useState(false);
  const [editCred, setEditCred]             = useState<IntegrationCredential | null>(null);
  const [credError, setCredError]           = useState<string | null>(null);

  const handleSetDefault = async (id: number) => {
    try {
      await apiService.setDefaultCredential(id);
      await onReload();
    } catch (e: unknown) {
      setCredError(e instanceof Error ? e.message : 'Failed to set default');
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!window.confirm(`Delete credential "${name}"? This cannot be undone.`)) return;
    try {
      await apiService.deleteCredential(id);
      await onReload();
    } catch (e: unknown) {
      setCredError(e instanceof Error ? e.message : 'Delete failed');
    }
  };

  const chDef = channelMap[channelId];

  return (
    <>
      <Divider sx={{ mt: 2.5 }} />
      <Box sx={{ pt: 2 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 1 }}>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Credential profiles</Typography>
            <Typography variant="caption" color="text.secondary">
              Multiple accounts for {chDef?.label ?? channelId}. Pass <code>credential_name</code> in your notification payload to use a specific profile.
            </Typography>
          </Box>
          <Button
            size="small"
            variant="outlined"
            startIcon={<Add sx={{ fontSize: 13 }} />}
            sx={{ flexShrink: 0, ml: 1.5 }}
            onClick={() => { setEditCred(null); setCredDialogOpen(true); }}
          >
            Add profile
          </Button>
        </Stack>

        {credError && <Alert severity="error" sx={{ mb: 1 }} onClose={() => setCredError(null)}>{credError}</Alert>}

        {credentials.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ py: 1, fontStyle: 'italic' }}>
            No credential profiles yet.
          </Typography>
        ) : (
          <TableContainer sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'background.paper' }}>
                  <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Profile name</TableCell>
                  <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Default</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {credentials.map(cred => (
                  <TableRow key={cred.id} hover>
                    <TableCell>
                      <Box component="code" sx={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: 'primary.main', bgcolor: 'action.hover', px: 0.75, py: 0.25, borderRadius: 0.5 }}>
                        {cred.name}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {cred.is_default ? (
                        <Chip size="small" label="Default" color="success" variant="outlined" icon={<Star sx={{ fontSize: '12px !important' }} />} />
                      ) : (
                        <Typography variant="caption" color="text.secondary">—</Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        {!cred.is_default && (
                          <Tooltip title="Set as default">
                            <IconButton size="small" onClick={() => void handleSetDefault(cred.id)}>
                              <StarBorder sx={{ fontSize: 16 }} />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="Edit">
                          <IconButton size="small" color="primary" onClick={() => { setEditCred(cred); setCredDialogOpen(true); }}>
                            <Edit sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton size="small" color="error" onClick={() => void handleDelete(cred.id, cred.name)}>
                            <Delete sx={{ fontSize: 16 }} />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      <CredentialDialog
        open={credDialogOpen}
        onClose={() => { setCredDialogOpen(false); setEditCred(null); }}
        onSaved={() => { void onReload(); }}
        initial={editCred}
        fixedChannel={channelId}
      />
    </>
  );
}

function buildEnvSnippet(fields: EnvFieldDef[], values: Record<string, string>): string {
  return fields
    .map((f) => {
      const v = (values[f.apiKey] ?? '').trim();
      return v ? `${f.envCopyName}=${v}` : '';
    })
    .filter(Boolean)
    .join('\n');
}

type CardRow = (typeof INTEGRATION_CARDS)[number];

type IntegrationConfigureDialogProps = {
  open: boolean;
  row: CardRow | null;
  onClose: () => void;
  integrationOn: IntegrationStatus | null;
  credentials: IntegrationCredential[];
  onCredentialsChange: () => Promise<void>;
};

function IntegrationConfigureDialog({
  open,
  row,
  onClose,
  integrationOn,
  credentials,
  onCredentialsChange,
}: IntegrationConfigureDialogProps) {
  const credChannelId = row ? CARD_CREDENTIAL_CHANNEL[row.key] : undefined;
  const [copyHint, setCopyHint] = useState<string | null>(null);

  useEffect(() => { if (!open) setCopyHint(null); }, [open]);

  if (!row) return null;

  const serverOn = Boolean(integrationOn?.[row.key]);

  const copySubscriberLine = async () => {
    try {
      await navigator.clipboard.writeText('SUBSCRIBER_REQUIRED=true');
      setCopyHint('Copied SUBSCRIBER_REQUIRED=true');
    } catch {
      setCopyHint('Could not copy.');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth={credChannelId ? 'md' : 'sm'} scroll="paper">
      <DialogTitle sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1, pr: 1 }}>
        <Box>
          <Typography component="span" variant="h6" sx={{ fontWeight: 600 }}>{row.title}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{row.subtitle}</Typography>
        </Box>
        <IconButton aria-label="Close" onClick={onClose} size="small"><Close /></IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Stack spacing={2} sx={{ pt: 0.5 }}>
          {/* Status row */}
          <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1}>
            <Typography variant="body2" color="text.secondary">Status</Typography>
            <Chip size="small" label={serverOn ? 'On' : 'Off'} color={serverOn ? 'success' : 'default'} variant={serverOn ? 'filled' : 'outlined'} />
          </Stack>

          {credChannelId ? (
            /* ── Channels that support named credentials ─────────────── */
            <ChannelCredentialsSection
              channelId={credChannelId}
              credentials={credentials.filter(c => c.channel === credChannelId)}
              onReload={onCredentialsChange}
            />
          ) : (
            /* ── Channels without credential profiles (redis, subscriber gate) ── */
            <>
              <Box sx={{ bgcolor: 'background.default', border: '1px solid', borderColor: 'divider', borderRadius: 1, px: 1.5, py: 1 }}>
                <Typography variant="caption" color="text.secondary">Env reference</Typography>
                <Box component="code" sx={{ display: 'block', mt: 0.25, fontSize: '0.75rem', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                  {row.envVar}
                </Box>
              </Box>
              {row.key === 'subscriber_required' && (
                <>
                  <Typography variant="body2" color="text.secondary">
                    When enabled, send endpoints require an existing subscriber record. Set the flag on the API server.
                  </Typography>
                  <Button startIcon={<ContentCopy />} variant="outlined" size="small" onClick={() => void copySubscriberLine()}>
                    Copy env line
                  </Button>
                </>
              )}
              {copyHint && <Typography variant="body2" color="text.secondary">{copyHint}</Typography>}
            </>
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

const Integrations: React.FC = () => {
  const [status, setStatus]             = useState<IntegrationStatus | null>(null);
  const [me, setMe]                     = useState<IntegrationMe | null>(null);
  const [error, setError]               = useState<string | null>(null);
  const [loading, setLoading]           = useState(true);
  const [configureKey, setConfigureKey] = useState<StatusKey | null>(null);
  const [credentials, setCredentials]   = useState<IntegrationCredential[]>([]);

  const load = useCallback(async () => {
    try {
      const s = await apiService.getIntegrationStatus();
      setStatus(s);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    }

    try {
      const m = await apiService.getIntegrationMe();
      setMe(m);
    } catch {
      setMe(null);
    }

    try {
      const creds = await apiService.listCredentials();
      setCredentials(creds ?? []);
    } catch {
      setCredentials([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const env = me?.environment ?? status;
  const configureRow = configureKey ? INTEGRATION_CARDS.find((c) => c.key === configureKey) ?? null : null;

  const enabledCount = INTEGRATION_CARDS.filter((c) => Boolean(env?.[c.key])).length;

  return (
    <Box sx={{ bgcolor: 'background.default', minHeight: '100%' }}>
      {/* ── Page header band ─────────────────────────────────────── */}
      <Box sx={{ bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider', px: { xs: 2, md: 3 }, pt: 2.5, pb: 2 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.75 }}>
          Console › Integrations
        </Typography>
        <Typography variant="h4">Integrations</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25, maxWidth: 760 }}>
          Connect outbound channels, AWS SES, and SMTP. Click a card to configure it. Saved values apply when you send
          with a signed-in session or a database API key.
        </Typography>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip size="small" variant="outlined" label={`${INTEGRATION_CARDS.length} channels`} />
          <Chip size="small" variant="outlined" label={`${enabledCount} enabled`} color={enabledCount > 0 ? 'success' : 'default'} />
        </Stack>
      </Box>

      {loading && !status && <LinearProgress />}

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Grid container spacing={2}>
          {INTEGRATION_CARDS.map((row) => {
            const on = Boolean(env?.[row.key]);
            return (
              <Grid item xs={12} sm={6} lg={4} key={row.key}>
                {(() => {
                  const credChId   = CARD_CREDENTIAL_CHANNEL[row.key];
                  const credCount  = credChId ? credentials.filter(c => c.channel === credChId).length : 0;
                  const defCred    = credChId ? credentials.find(c => c.channel === credChId && c.is_default) : undefined;
                  return (
                    <Paper
                      variant="outlined"
                      sx={{
                        height: '100%',
                        borderRadius: 1,
                        overflow: 'hidden',
                        bgcolor: 'background.paper',
                        border: '1px solid',
                        borderColor: 'divider',
                        transition: 'border-color 0.15s, box-shadow 0.15s',
                        '&:hover': {
                          borderColor: '#0972d3',
                          boxShadow: '0 2px 8px rgba(9,114,211,0.1)',
                        },
                      }}
                    >
                      <CardActionArea
                        onClick={() => setConfigureKey(row.key)}
                        sx={{ height: '100%', p: 2.5, display: 'flex', gap: 2, alignItems: 'flex-start' }}
                      >
                        <IntegrationLogo
                          iconUrls={row.iconUrls}
                          iconLocalFile={row.iconLocalFile}
                          letter={row.letter}
                          brandColor={row.brandColor}
                          useLock={row.useLock}
                        />
                        <Box sx={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
                          <Stack direction="row" alignItems="flex-start" justifyContent="space-between" gap={1} sx={{ mb: 0.5 }}>
                            <Box>
                              <Typography variant="body1" sx={{ fontWeight: 700, lineHeight: 1.3 }}>
                                {row.title}
                              </Typography>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                                {row.subtitle}
                              </Typography>
                            </Box>
                            <Chip
                              size="small"
                              label={on ? 'On' : 'Off'}
                              color={on ? 'success' : 'default'}
                              variant="outlined"
                              sx={{ flexShrink: 0, fontWeight: 700 }}
                            />
                          </Stack>
                          <Box
                            component="code"
                            sx={{
                              display: 'block',
                              mt: 1,
                              fontSize: '0.7rem',
                              fontFamily: 'monospace',
                              color: 'text.secondary',
                              wordBreak: 'break-all',
                              bgcolor: 'background.default',
                              border: '1px solid',
                              borderColor: 'divider',
                              borderRadius: 0.5,
                              px: 0.75,
                              py: 0.5,
                            }}
                          >
                            {row.envVar}
                          </Box>
                          {credChId && credCount > 0 && (
                            <Stack direction="row" spacing={0.5} sx={{ mt: 1 }} flexWrap="wrap">
                              <Chip
                                size="small"
                                label={`${credCount} profile${credCount !== 1 ? 's' : ''}`}
                                color="primary"
                                variant="outlined"
                                sx={{ height: 18, fontSize: '0.68rem', fontWeight: 600 }}
                              />
                              {defCred && (
                                <Chip
                                  size="small"
                                  icon={<Star sx={{ fontSize: '10px !important' }} />}
                                  label={defCred.name}
                                  color="success"
                                  variant="outlined"
                                  sx={{ height: 18, fontSize: '0.68rem' }}
                                />
                              )}
                            </Stack>
                          )}
                        </Box>
                      </CardActionArea>
                    </Paper>
                  );
                })()}
              </Grid>
            );
          })}
        </Grid>
      </Box>

      <IntegrationConfigureDialog
        open={Boolean(configureRow)}
        row={configureRow}
        onClose={() => setConfigureKey(null)}
        integrationOn={env}
        credentials={credentials}
        onCredentialsChange={() => load()}
      />
    </Box>
  );
};

export default Integrations;
