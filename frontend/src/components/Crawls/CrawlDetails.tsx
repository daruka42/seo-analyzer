import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  IconButton,
  LinearProgress,
  Chip,
  Button,
  Alert,
  Tab,
  Tabs,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  Stop as StopIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService, CrawlSession } from '../../services/api';
import CrawlProgress from './CrawlProgress';
import CrawlSummary from './CrawlSummary';
import PagesList from './PagesList';
import IssuesList from './IssuesList';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`crawl-tabpanel-${index}`}
      aria-labelledby={`crawl-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const CrawlDetails: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<CrawlSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (sessionId) {
      fetchSession();
    }
  }, [sessionId]);

  useEffect(() => {
    // Auto-refresh for running crawls
    if (autoRefresh && session?.status === 'running') {
      intervalRef.current = setInterval(() => {
        fetchSession();
      }, 5000); // Refresh every 5 seconds
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, session?.status]);

  const fetchSession = async () => {
    if (!sessionId) return;

    try {
      if (loading) setLoading(true);
      const sessionData = await apiService.getCrawlSession(sessionId);
      setSession(sessionData);
      
      // Stop auto-refresh when crawl is complete
      if (sessionData.status === 'completed' || sessionData.status === 'failed') {
        setAutoRefresh(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch crawl details');
      setAutoRefresh(false);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'info';
      case 'failed':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading && !session) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !session) {
    return (
      <Box>
        <Box display="flex" alignItems="center" mb={4}>
          <IconButton onClick={() => navigate(-1)} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4">Crawl Details</Typography>
        </Box>
        <Alert severity="error">{error || 'Crawl session not found'}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={4}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate(-1)} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" component="h1" fontWeight="bold">
              Crawl Details
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Session: {session.id}
            </Typography>
          </Box>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <Chip 
            label={session.status.charAt(0).toUpperCase() + session.status.slice(1)} 
            color={getStatusColor(session.status)} 
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchSession}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Progress Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <CrawlProgress session={session} />
        </CardContent>
      </Card>

      {/* Error Message */}
      {session.error_message && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {session.error_message}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Summary" />
          <Tab label="Pages" />
          <Tab label="Issues" />
          <Tab label="Configuration" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <CrawlSummary sessionId={session.id} />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <PagesList sessionId={session.id} />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <IssuesList sessionId={session.id} />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Crawl Configuration
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Max URLs</Typography>
                <Typography variant="h6">{session.config.max_urls}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Max Depth</Typography>
                <Typography variant="h6">{session.config.max_depth}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Delay</Typography>
                <Typography variant="h6">{session.config.delay}s</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">JavaScript</Typography>
                <Typography variant="h6">
                  {session.config.render_javascript ? 'Enabled' : 'Disabled'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default CrawlDetails;
