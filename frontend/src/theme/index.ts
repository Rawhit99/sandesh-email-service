import { createTheme, ThemeOptions } from '@mui/material/styles';

/* ─────────────────────────────────────────
   AWS Console Design Tokens (exact parity)
   ───────────────────────────────────────── */

function makeThemeOptions(mode: 'light' | 'dark'): ThemeOptions {
  const isDark = mode === 'dark';

  /* ── palette ─── */
  const bg     = isDark ? '#0b1220' : '#f0f2f2';
  const paper  = isDark ? '#121a27' : '#ffffff';
  const border  = isDark ? '#263245' : '#d5dbdb';
  const divider = isDark ? '#263245' : '#d5dbdb';
  const textPrimary   = isDark ? '#e6edf3' : '#16191f';
  const textSecondary = isDark ? '#9fb0c3' : '#545b64';

  return {
    spacing: 4,
    palette: {
      mode,
      primary:   { main: '#0972d3', light: '#539fe5', dark: '#05508a', contrastText: '#ffffff' },
      secondary: { main: '#545b64', light: '#879596', dark: '#3a4047', contrastText: '#ffffff' },
      success:   { main: '#1d8102', light: '#4f9f36', dark: '#126400', contrastText: '#ffffff' },
      warning:   { main: '#ec7211', light: '#f2994a', dark: '#b65607', contrastText: '#ffffff' },
      error:     { main: '#d91515', light: '#e64a4a', dark: '#a61c1c', contrastText: '#ffffff' },
      background: { default: bg, paper },
      text: { primary: textPrimary, secondary: textSecondary },
      action: {
        hover: isDark ? 'rgba(159, 176, 195, 0.12)' : 'rgba(22, 25, 31, 0.04)',
        selected: isDark ? 'rgba(9, 114, 211, 0.2)' : 'rgba(9, 114, 211, 0.12)',
      },
      divider,
      grey: {
        50: '#fafafa', 100: '#f0f2f2', 200: '#eaeded', 300: '#d5dbdb',
        400: '#aab7b8', 500: '#879596', 600: '#687078',
        700: '#545b64', 800: '#3a4047', 900: '#16191f',
      },
    },

    typography: {
      fontFamily: [
        '"Amazon Ember"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"',
        'Inter', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif',
      ].join(','),
      h1: { fontSize: '2.25rem', fontWeight: 700, lineHeight: 1.2 },
      h2: { fontSize: '1.875rem', fontWeight: 700, lineHeight: 1.25 },
      h3: { fontSize: '1.5rem',   fontWeight: 700, lineHeight: 1.3 },
      h4: { fontSize: '1.25rem',  fontWeight: 700, lineHeight: 1.35 },
      h5: { fontSize: '1.125rem', fontWeight: 700, lineHeight: 1.4 },
      h6: { fontSize: '1rem',     fontWeight: 700, lineHeight: 1.4 },
      body1: { fontSize: '0.9375rem', lineHeight: 1.5, fontWeight: 400 },
      body2: { fontSize: '0.875rem',  lineHeight: 1.45, fontWeight: 400 },
      button: { fontSize: '0.8125rem', fontWeight: 600, textTransform: 'none' as const },
      caption: { fontSize: '0.75rem', lineHeight: 1.5, fontWeight: 400 },
      overline: { fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.08em' },
    },

    shape: { borderRadius: 4 },

    shadows: [
      'none',
      '0 1px 1px rgba(0,0,0,0.04)',
      '0 1px 4px rgba(0,0,0,0.07)',
      '0 2px 6px rgba(0,0,0,0.10)',
      '0 4px 12px rgba(0,0,0,0.12)',
      ...Array(20).fill('0 4px 12px rgba(0,0,0,0.12)'),
    ] as any,

    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: bg,
            color: textPrimary,
          },
          '::-webkit-scrollbar-track': {
            background: isDark ? '#0f1826' : '#f0f2f2',
          },
          '::-webkit-scrollbar-thumb': {
            background: isDark ? '#425063' : '#aab7b8',
          },
        },
      },
      /* ── Table ── */
      MuiTableCell: {
        styleOverrides: {
          root: {
            paddingTop: 10, paddingBottom: 10, paddingLeft: 16, paddingRight: 16,
            fontSize: '0.8125rem',
            borderBottom: `1px solid ${isDark ? '#2a3443' : '#eaeded'}`,
            color: textPrimary,
            backgroundColor: paper,
          },
          head: {
            fontWeight: 700, color: textPrimary,
            backgroundColor: isDark ? '#162032' : '#fafafa',
            borderBottom: `1px solid ${border}`,
            fontSize: '0.8125rem',
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            '&:hover': { backgroundColor: isDark ? '#1a2d42' : '#f8f8f8' },
            '&:last-child td': { borderBottom: 0 },
          },
        },
      },
      MuiTableContainer: {
        styleOverrides: {
          root: { backgroundColor: paper },
        },
      },

      /* ── Tabs ── */
      MuiTabs: {
        styleOverrides: {
          root: { borderBottom: `1px solid ${border}`, backgroundColor: paper },
          indicator: { height: 2, backgroundColor: '#0972d3' },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            minHeight: 44, fontSize: '0.8125rem', fontWeight: 600,
            textTransform: 'none', color: textSecondary, padding: '10px 16px',
            '&.Mui-selected': { color: '#0972d3' },
          },
        },
      },

      /* ── Inputs ── */
      MuiFormControl: { defaultProps: { size: 'small' } },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? '#162032' : '#ffffff',
            '& .MuiOutlinedInput-notchedOutline': { borderColor: isDark ? '#2a3443' : '#aab7b8' },
            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: isDark ? '#879596' : '#687078' },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#0972d3', borderWidth: '1.5px' },
            color: textPrimary,
          },
          notchedOutline: { borderColor: isDark ? '#2a3443' : '#aab7b8' },
        },
      },
      MuiInputLabel: {
        styleOverrides: { root: { color: textSecondary } },
      },
      MuiInputBase: {
        styleOverrides: { root: { color: textPrimary } },
      },
      MuiTextField: {
        defaultProps: { size: 'small' },
      },
      MuiSelect: {
        styleOverrides: {
          icon: { color: textSecondary },
        },
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            fontSize: '0.8125rem',
            backgroundColor: paper,
            color: textPrimary,
            '&:hover': { backgroundColor: isDark ? '#1a2d42' : '#f0f2f2' },
            '&.Mui-selected': { backgroundColor: isDark ? '#1a3a5c' : '#eff6ff' },
          },
        },
      },

      /* ── Buttons ── */
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none', fontWeight: 600, padding: '7px 16px',
            borderRadius: 4, fontSize: '0.8125rem', boxShadow: 'none',
            '&:hover': { boxShadow: 'none' },
          },
          contained: { boxShadow: 'none', '&:hover': { boxShadow: 'none' } },
          containedPrimary: {
            backgroundColor: '#ec7211', color: '#ffffff',
            '&:hover': { backgroundColor: '#d46a10' },
            '&.Mui-disabled': { backgroundColor: isDark ? '#2a3443' : '#f0f2f2', color: isDark ? '#545b64' : '#aab7b8' },
          },
          outlined: {
            borderColor: isDark ? '#2a3443' : '#aab7b8',
            color: textPrimary,
            backgroundColor: isDark ? '#162032' : '#ffffff',
            '&:hover': { borderColor: isDark ? '#879596' : '#687078', backgroundColor: isDark ? '#1a2d42' : '#f8f8f8' },
          },
          outlinedPrimary: {
            borderColor: '#0972d3', color: '#0972d3',
            backgroundColor: isDark ? '#162032' : '#ffffff',
            '&:hover': { backgroundColor: isDark ? '#1a3a5c' : '#eff6ff' },
          },
          text: { color: '#0972d3', '&:hover': { backgroundColor: isDark ? '#1a3a5c' : '#eff6ff' } },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: { color: textSecondary },
        },
      },

      /* ── Cards / Paper ── */
      MuiCard: {
        styleOverrides: {
          root: { boxShadow: 'none', borderRadius: 8, border: `1px solid ${border}`, backgroundColor: paper },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: { borderRadius: 8, border: `1px solid ${border}`, boxShadow: 'none', backgroundColor: paper },
          elevation0: { border: `1px solid ${border}` },
        },
      },

      /* ── Chip ── */
      MuiChip: {
        styleOverrides: {
          root: { borderRadius: 4, fontWeight: 500, fontSize: '0.75rem', height: 22 },
          outlined: { borderColor: isDark ? '#2a3443' : '#aab7b8', color: textSecondary, backgroundColor: 'transparent' },
          colorSuccess: { color: '#1d8102', borderColor: '#1d8102', backgroundColor: isDark ? '#0a2210' : '#f2f9f2' },
          colorError:   { color: '#d91515', borderColor: '#d91515', backgroundColor: isDark ? '#2a0808' : '#fdf0f0' },
          colorWarning: { color: '#b65607', borderColor: '#ec7211', backgroundColor: isDark ? '#2a1408' : '#fef6ee' },
          colorPrimary: { color: '#0972d3', borderColor: '#0972d3', backgroundColor: isDark ? '#08203a' : '#eff6ff' },
        },
      },

      /* ── Dialogs ── */
      MuiDialog: {
        styleOverrides: {
          paper: { backgroundColor: paper, border: `1px solid ${border}` },
        },
      },
      MuiDialogTitle: {
        styleOverrides: {
          root: {
            fontSize: '1rem', fontWeight: 700, padding: '16px 20px 12px',
            borderBottom: `1px solid ${border}`, color: textPrimary,
          },
        },
      },
      MuiDialogContent: {
        styleOverrides: { root: { padding: '16px 20px', backgroundColor: paper } },
      },
      MuiDialogActions: {
        styleOverrides: {
          root: { padding: '12px 20px 16px', borderTop: `1px solid ${border}`, backgroundColor: paper },
        },
      },

      /* ── AppBar ── */
      MuiAppBar: {
        styleOverrides: {
          root: { boxShadow: 'none', borderBottom: `1px solid ${border}` },
        },
      },

      /* ── Drawer ── */
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: `1px solid ${border}`, boxShadow: 'none',
            backgroundColor: isDark ? '#16212e' : '#ffffff',
            color: textPrimary,
          },
        },
      },

      /* ── List nav ── */
      MuiListItem: {
        styleOverrides: {
          root: {
            borderRadius: 4, margin: '1px 6px',
            '&.Mui-selected': {
              backgroundColor: isDark ? '#1a3a5c' : '#ecf3fb',
              color: '#0972d3',
              borderLeft: '2px solid #0972d3',
              '&:hover': { backgroundColor: isDark ? '#1a3a5c' : '#e3eef9' },
              '& .MuiListItemIcon-root': { color: '#0972d3' },
            },
            '&:hover': { backgroundColor: isDark ? '#1a2d42' : '#f0f2f2' },
          },
        },
      },
      MuiListItemIcon: { styleOverrides: { root: { minWidth: 32 } } },
      MuiListItemText: {
        styleOverrides: {
          primary: { color: textPrimary, fontSize: '0.8125rem' },
        },
      },

      /* ── Alert ── */
      MuiAlert: { styleOverrides: { root: { borderRadius: 4, border: '1px solid' } } },

      /* ── LinearProgress ── */
      MuiLinearProgress: { styleOverrides: { root: { borderRadius: 0, height: 3 } } },

      /* ── Divider ── */
      MuiDivider: {
        styleOverrides: { root: { borderColor: isDark ? '#2a3443' : '#eaeded' } },
      },
    },
  };
}

export function createAppTheme(mode: 'light' | 'dark') {
  return createTheme(makeThemeOptions(mode));
}

/* legacy export kept for anything that still imports `theme` directly */
export const theme = createAppTheme('light');
