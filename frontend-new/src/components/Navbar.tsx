import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
} from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import SendIcon from '@mui/icons-material/Send';

const Navbar = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <EmailIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          SANDESH
        </Typography>
        <Box>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/send-email"
            startIcon={<SendIcon />}
          >
            Send Email
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/templates"
          >
            Templates
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/settings"
          >
            Settings
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 