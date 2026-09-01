import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#0066A1',
      dark: '#004F7C',
      light: '#EAF5FA',
    },
    secondary: {
      main: '#78BE20',
      dark: '#4F8F18',
      light: '#EEF7E5',
    },
    success: {
      main: '#2E7D32',
    },
    warning: {
      main: '#ED8B00',
    },
    error: {
      main: '#D32F2F',
    },
    info: {
      main: '#0288D1',
    },
    background: {
      default: '#F7F9FB',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1F2933',
      secondary: '#667085',
      disabled: '#98A2B3',
    },
    divider: '#E1E7EC',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 600,
      fontSize: '2.5rem',
    },
    h2: {
      fontWeight: 600,
      fontSize: '2rem',
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.04)',
          border: '1px solid #E1E7EC',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

export default theme;
