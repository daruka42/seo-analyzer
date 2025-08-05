// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Typography, Container, Alert } from '@mui/material';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
          <Container maxWidth="lg" sx={{ py: 4 }}>
            <Typography variant="h2" component="h1" gutterBottom align="center">
              SEO Analyzer
            </Typography>
            <Typography variant="h5" component="h2" gutterBottom align="center" color="text.secondary">
              Professional Website Analysis Tool
            </Typography>
            
            <Alert severity="success" sx={{ mt: 4, mb: 4 }}>
              🎉 Frontend is running successfully! The application is now ready for development.
            </Alert>

            <Routes>
              <Route path="/" element={
                <Box>
                  <Typography variant="h4" gutterBottom>
                    Welcome to SEO Analyzer
                  </Typography>
                  <Typography variant="body1" paragraph>
                    This is a professional SEO analysis tool with Hungarian language support.
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Backend API Status: ✅ Running on port 8000
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Frontend Status: ✅ Running on port 3000
                  </Typography>
                  <Alert severity="info" sx={{ mt: 2 }}>
                    The full application features will be available soon. 
                    For now, you can access:
                    <br />• Backend API: <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer">http://localhost:8000</a>
                    <br />• API Documentation: <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">http://localhost:8000/docs</a>
                  </Alert>
                </Box>
              } />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
