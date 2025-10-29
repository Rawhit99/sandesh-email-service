import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Snackbar,
  Alert,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import apiService, { EmailTemplate } from '../services/api';
import { DataGrid } from '@mui/x-data-grid';

const EmailTemplates = () => {
  const [open, setOpen] = useState(false);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const templatesList = await apiService.getTemplates();
      setTemplates(templatesList);
    } catch (err) {
      setError('Failed to load templates');
      console.error('Error loading templates:', err);
    }
  };

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const formatTemplateName = (templateId: string) => {
    return templateId
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 90 },
    { field: 'template_id', headerName: 'Template ID', width: 150 },
    { field: 'subject', headerName: 'Subject', width: 200 },
    { field: 'body', headerName: 'Content', width: 400 },
    { 
      field: 'created_at', 
      headerName: 'Created At', 
      width: 200,
      valueFormatter: (params: any) => new Date(params.value).toLocaleString()
    },
    { 
      field: 'updated_at', 
      headerName: 'Updated At', 
      width: 200,
      valueFormatter: (params: any) => new Date(params.value).toLocaleString()
    },
    { field: 'is_active', headerName: 'Status', width: 100 },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      renderCell: (params: any) => (
        <>
          <IconButton edge="end" aria-label="edit">
            <EditIcon />
          </IconButton>
          <IconButton edge="end" aria-label="delete">
            <DeleteIcon />
          </IconButton>
        </>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Email Templates</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleClickOpen}
        >
          New Template
        </Button>
      </Box>

      <Paper>
        <DataGrid
          rows={templates}
          columns={columns}
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 10 },
            },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Create New Template</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Template ID"
            fullWidth
            variant="outlined"
            helperText="Enter a unique identifier for the template (e.g., welcome_email)"
          />
          <TextField
            margin="dense"
            label="Subject"
            fullWidth
            variant="outlined"
          />
          <TextField
            margin="dense"
            label="Content"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleClose} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EmailTemplates; 