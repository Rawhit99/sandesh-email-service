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
  IconButton,
  InputAdornment,
  LinearProgress,
  Paper,
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
  Business as BusinessIcon,
  CheckCircle as CheckCircleIcon,
  Edit as EditIcon,
  LayersOutlined as TemplatesIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import apiService, { OrgTemplateSetting, PlatformOrganization } from '../services/api';

/* ── Org Templates Dialog ────────────────────────────────────────────────── */

interface OrgTemplatesDialogProps {
  open: boolean;
  org: PlatformOrganization | null;
  onClose: () => void;
}

function OrgTemplatesDialog({ open, org, onClose }: OrgTemplatesDialogProps) {
  const [templates, setTemplates]   = useState<OrgTemplateSetting[]>([]);
  const [loading, setLoading]       = useState(false);
  const [saving, setSaving]         = useState<string | null>(null);  // template_id being saved
  const [bulkBusy, setBulkBusy]     = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const [success, setSuccess]       = useState<string | null>(null);
  const [search, setSearch]         = useState('');

  const load = useCallback(async () => {
    if (!org) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.listOrgTemplates(org.id);
      setTemplates(data ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  }, [org]);

  useEffect(() => {
    if (open) { setSearch(''); setSuccess(null); setError(null); void load(); }
  }, [open, load]);

  const handleToggle = async (templateId: string, current: boolean) => {
    if (!org) return;
    setSaving(templateId);
    try {
      await apiService.updateOrgTemplateSetting(org.id, templateId, !current);
      setTemplates(prev => prev.map(t => t.template_id === templateId ? { ...t, is_enabled: !current } : t));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Update failed');
    } finally {
      setSaving(null);
    }
  };

  const handleBulk = async (enable: boolean) => {
    if (!org) return;
    setBulkBusy(true);
    setError(null);
    try {
      await apiService.bulkUpdateOrgTemplates(org.id, enable);
      setTemplates(prev => prev.map(t => ({ ...t, is_enabled: enable })));
      setSuccess(enable ? 'All templates enabled.' : 'All templates disabled.');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Bulk update failed');
    } finally {
      setBulkBusy(false);
    }
  };

  const filtered = templates.filter(t =>
    t.template_name.toLowerCase().includes(search.toLowerCase()) ||
    t.template_id.toLowerCase().includes(search.toLowerCase()),
  );
  const enabledCount  = templates.filter(t => t.is_enabled).length;
  const disabledCount = templates.length - enabledCount;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth scroll="paper">
      <DialogTitle sx={{ pb: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          Template scope — {org?.name}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
          Control which templates this organisation can use. Disabled templates are blocked at send time.
        </Typography>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0 }}>
        {/* Toolbar */}
        <Box sx={{ px: 2.5, py: 1.5, bgcolor: 'background.paper', borderBottom: '1px solid', borderColor: 'divider' }}>
          <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap">
            <TextField
              size="small"
              placeholder="Search templates…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              sx={{ flex: 1, minWidth: 200, maxWidth: 360 }}
              InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon sx={{ fontSize: 16, color: 'text.secondary' }} /></InputAdornment> }}
            />
            <Box sx={{ flex: 1 }} />
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip size="small" variant="outlined" label={`${enabledCount} enabled`}  color="success" />
              {disabledCount > 0 && (
                <Chip size="small" variant="outlined" label={`${disabledCount} disabled`} color="error" />
              )}
            </Stack>
            <Button
              size="small"
              variant="outlined"
              color="success"
              disabled={bulkBusy || templates.length === 0}
              startIcon={<CheckCircleIcon sx={{ fontSize: 14 }} />}
              onClick={() => void handleBulk(true)}
            >
              Enable all
            </Button>
            <Button
              size="small"
              variant="outlined"
              color="error"
              disabled={bulkBusy || templates.length === 0}
              onClick={() => void handleBulk(false)}
            >
              Disable all
            </Button>
          </Stack>
        </Box>

        {/* Alerts */}
        {error   && <Alert severity="error"   sx={{ mx: 2.5, mt: 1.5 }} onClose={() => setError(null)}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mx: 2.5, mt: 1.5 }} onClose={() => setSuccess(null)}>{success}</Alert>}

        {/* Table */}
        {loading ? (
          <Box sx={{ py: 6, textAlign: 'center' }}><CircularProgress size={28} /></Box>
        ) : filtered.length === 0 ? (
          <Box sx={{ py: 6, textAlign: 'center' }}>
            <TemplatesIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.35, mb: 1.5 }} />
            <Typography variant="h6" color="text.secondary">
              {templates.length === 0 ? 'No templates in this organisation yet' : 'No templates match your search'}
            </Typography>
            {templates.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Switch to this organisation and create templates first
              </Typography>
            )}
          </Box>
        ) : (
          <TableContainer component={Paper} sx={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ pl: 2.5 }}>Template</TableCell>
                  <TableCell>Template ID</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Template status</TableCell>
                  <TableCell align="center">Enabled for org</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filtered.map(t => (
                  <TableRow key={t.template_id} hover sx={{ opacity: t.is_enabled ? 1 : 0.55 }}>
                    <TableCell sx={{ pl: 2.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>{t.template_name}</Typography>
                    </TableCell>
                    <TableCell>
                      <Box component="code" sx={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'primary.main', bgcolor: 'action.hover', px: 0.75, py: 0.25, borderRadius: 0.5 }}>
                        {t.template_id}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 220 }} title={t.subject}>{t.subject}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={t.is_active ? 'Active' : 'Inactive'}
                        color={t.is_active ? 'success' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title={t.is_enabled ? 'Click to disable for this org' : 'Click to enable for this org'}>
                        <Switch
                          size="small"
                          checked={t.is_enabled}
                          disabled={saving === t.template_id || bulkBusy}
                          onChange={() => void handleToggle(t.template_id, t.is_enabled)}
                          color="success"
                        />
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        <Divider />
        <Box sx={{ px: 2.5, py: 1.5, bgcolor: 'background.paper' }}>
          <Typography variant="caption" color="text.secondary">
            Toggling a template here does not delete it — it only controls whether sends from this organisation are allowed to use it. Default (no override) = <strong>enabled</strong>.
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

const Organizations: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [rows, setRows] = useState<PlatformOrganization[]>([]);

  // Create form
  const [name, setName] = useState('');
  const [orgSlug, setOrgSlug] = useState('');
  const [busy, setBusy] = useState(false);

  // Edit dialog
  const [editOpen, setEditOpen] = useState(false);
  const [editOrg, setEditOrg]   = useState<PlatformOrganization | null>(null);
  const [editName, setEditName] = useState('');
  const [editSlug, setEditSlug] = useState('');
  const [editBusy, setEditBusy] = useState(false);

  // Templates dialog
  const [tplOpen, setTplOpen] = useState(false);
  const [tplOrg, setTplOrg]   = useState<PlatformOrganization | null>(null);

  const load = useCallback(async (background = false) => {
    background ? setRefreshing(true) : setLoading(true);
    setError(null);
    try {
      const list = await apiService.listPlatformOrganizations();
      setRows(list);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load organizations');
    } finally {
      background ? setRefreshing(false) : setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const onCreate = async () => {
    setMsg(null);
    setError(null);
    setBusy(true);
    try {
      await apiService.createPlatformOrganization({
        name: name.trim(),
        org_slug: orgSlug.trim() || undefined,
      });
      setName('');
      setOrgSlug('');
      setMsg('Organization created. Select it in the top bar to manage templates and integrations.');
      await load(true);
      window.dispatchEvent(new Event('sandesh-platform-orgs-refresh'));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Create failed');
    } finally {
      setBusy(false);
    }
  };

  const openEdit = (org: PlatformOrganization) => {
    setEditOrg(org);
    setEditName(org.name);
    setEditSlug(org.org_slug || '');
    setEditOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editOrg) return;
    setEditBusy(true);
    try {
      await apiService.updatePlatformOrganization(editOrg.id, {
        name: editName.trim() || undefined,
        org_slug: editSlug.trim() || undefined,
      });
      setEditOpen(false);
      setMsg('Organization updated.');
      await load(true);
      window.dispatchEvent(new Event('sandesh-platform-orgs-refresh'));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Update failed');
    } finally {
      setEditBusy(false);
    }
  };

  // Auto-derive slug from name while user types (only when slug is empty)
  const handleNameChange = (v: string) => {
    setName(v);
    if (!orgSlug) {
      setOrgSlug(v.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40));
    }
  };

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
          Console › Organizations
        </Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h4">Customer organizations</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              Each org gets a dedicated tenant account for templates, integrations, and notifications
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon sx={{ fontSize: 15 }} />}
            onClick={() => void load(true)}
            disabled={refreshing}
            size="small"
          >
            Refresh
          </Button>
        </Stack>

        {/* Summary strip */}
        <Stack direction="row" spacing={1} sx={{ mt: 1.75 }} flexWrap="wrap">
          <Chip size="small" variant="outlined" label={`${rows.length} organizations`} />
          <Chip size="small" variant="outlined" label={`${rows.filter(r => r.has_tenant_account).length} ready`} color="success" />
        </Stack>
      </Box>

      {refreshing && <LinearProgress />}

      {/* ── Content area ─────────────────────────────────────────── */}
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {error && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
        {msg   && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg}</Alert>}

        {/* Create panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 2.5, mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 0.5 }}>Create organization</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 680 }}>
            Provide a display name and an optional short ID (slug). The slug is used as an identifier in API headers
            (<code>X-Sandesh-Organization-Id</code>) and credential selectors. It is auto-derived from the name if left blank.
          </Typography>
          <Stack direction="row" spacing={1.5} flexWrap="wrap" alignItems="flex-end">
            <TextField
              label="Organization name"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              size="small"
              sx={{ minWidth: 240 }}
              placeholder="e.g. Acme Corporation"
            />
            <TextField
              label="Organization ID (slug)"
              value={orgSlug}
              onChange={(e) => setOrgSlug(e.target.value.toLowerCase().replace(/[^a-z0-9\-_]/g, '-').slice(0, 60))}
              size="small"
              sx={{ minWidth: 200 }}
              placeholder="e.g. acme-corp"
              helperText="Lowercase letters, numbers and hyphens"
            />
            <Button
              variant="contained"
              startIcon={<AddIcon sx={{ fontSize: 15 }} />}
              disabled={busy || name.trim().length < 2}
              onClick={() => void onCreate()}
              size="small"
              sx={{ mb: '20px' }}
            >
              {busy ? 'Creating…' : 'Create'}
            </Button>
          </Stack>
        </Box>

        {/* Table panel */}
        <Box sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
          {rows.length === 0 ? (
            <Box sx={{ py: 8, textAlign: 'center' }}>
              <BusinessIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1.5, opacity: 0.4 }} />
              <Typography variant="h6" color="text.secondary">No organizations yet</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Create your first customer organization above
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} sx={{ border: 'none', borderRadius: 0, boxShadow: 'none' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Organization ID (slug)</TableCell>
                    <TableCell>Tenant service user</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>{r.id}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>{r.name}</Typography>
                      </TableCell>
                      <TableCell>
                        {r.org_slug ? (
                          <Box component="code" sx={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: 'primary.main', bgcolor: 'action.hover', px: 0.75, py: 0.25, borderRadius: 0.5 }}>
                            {r.org_slug}
                          </Box>
                        ) : (
                          <Typography variant="caption" color="text.secondary">—</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box component="code" sx={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: 'primary.main' }}>
                          {r.service_username ?? '—'}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          variant="outlined"
                          label={r.has_tenant_account ? 'Ready' : 'Pending'}
                          color={r.has_tenant_account ? 'success' : 'warning'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="Manage template scope">
                            <IconButton size="small" color="primary" onClick={() => { setTplOrg(r); setTplOpen(true); }}>
                              <TemplatesIcon sx={{ fontSize: 16 }} />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit organization">
                            <IconButton size="small" onClick={() => openEdit(r)}>
                              <EditIcon sx={{ fontSize: 16 }} />
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
      </Box>

      {/* ── Org Templates dialog ────────────────────────────────── */}
      <OrgTemplatesDialog
        open={tplOpen}
        org={tplOrg}
        onClose={() => setTplOpen(false)}
      />

      {/* ── Edit dialog ─────────────────────────────────────────── */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit organization</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 0.5 }}>
            <TextField
              label="Organization name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              size="small"
              fullWidth
            />
            <TextField
              label="Organization ID (slug)"
              value={editSlug}
              onChange={(e) => setEditSlug(e.target.value.toLowerCase().replace(/[^a-z0-9\-_]/g, '-').slice(0, 60))}
              size="small"
              fullWidth
              helperText="Lowercase letters, numbers and hyphens (2–60 chars)"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" size="small" onClick={() => setEditOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            size="small"
            disabled={editBusy || editName.trim().length < 2}
            onClick={() => void handleSaveEdit()}
          >
            {editBusy ? 'Saving…' : 'Save changes'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Organizations;
