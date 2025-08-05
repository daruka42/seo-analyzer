import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Grid,
  Chip,
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Speed as SpeedIcon,
  CheckCircle as CompleteIcon,
} from '@mui/icons-material';
import { CrawlSession } from '../../services/api';

interface CrawlProgressProps {
  session: CrawlSession;
}

const CrawlProgress: React.FC<CrawlProgressProps> = ({ session }) => {
  const progress = session.total_urls > 0 
    ? (session.crawled_urls / session.total_urls) * 100 
    : 0;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const calculateDuration = () => {
    const start = new Date(session.started_at);
    const end = session.completed_at ? new Date(session.completed_at) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);
    
    if (diffMins > 0) {
      return `${diffMins}m ${diffSecs}s`;
    }
    return `${diffSecs}s`;
  };

  const estimateTimeRemaining = () => {
    if (session.status !== 'running' || session.crawled_urls === 0) {
      return null;
    }

    const elapsed = new Date().getTime() - new Date(session.started_at).getTime();
    const ratePerMs = session.crawled_urls / elapsed;
    const remaining = session.total_urls - session.crawled_urls;
    const estimatedMs = remaining / ratePerMs;
    
    const estimatedMins = Math.floor(estimatedMs / 60000);
    const estimatedSecs = Math.floor((estimatedMs % 60000) / 1000);
    
    if (estimatedMins > 0) {
      return `~${estimatedMins}m ${estimatedSecs}s remaining`;
    }
    return `~${estimatedSecs}s remaining`;
  };

  return (
    <Box>
      <Grid container spacing={3} alignItems="center">
        <Grid item xs={12} md={8}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">
              Crawl Progress
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {session.crawled_urls} / {session.total_urls || '?'} pages
            </Typography>
          </Box>
          
          <LinearProgress 
            variant={session.total_urls > 0 ? "determinate" : "indeterminate"}
            value={progress} 
            sx={{ height: 8, borderRadius: 4, mb: 2 }}
          />
          
          {session.status === 'running' && estimateTimeRemaining() && (
            <Typography variant="body2" color="text.secondary">
              {estimateTimeRemaining()}
            </Typography>
          )}
        </Grid>

        <Grid item xs={12} md={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Box display="flex" alignItems="center" gap={1}>
                <ScheduleIcon fontSize="small" color="action" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Started
                  </Typography>
                  <Typography variant="body2">
                    {formatDate(session.started_at)}
                  </Typography>
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Box display="flex" alignItems="center" gap={1}>
                <SpeedIcon fontSize="small" color="action" />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Duration
                  </Typography>
                  <Typography variant="body2">
                    {calculateDuration()}
                  </Typography>
                </Box>
              </Box>
            </Grid>

            {session.completed_at && (
              <Grid item xs={12}>
                <Box display="flex" alignItems="center" gap={1}>
                  <CompleteIcon fontSize="small" color="success" />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Completed
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(session.completed_at)}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            )}
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CrawlProgress;
