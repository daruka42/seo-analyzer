import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Pages as PagesIcon,
  BugReport as IssuesIcon,
  Speed as SpeedIcon,
  TrendingUp as TrendIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { apiService } from '../../services/api';

interface CrawlSummaryProps {
  sessionId: string;
}

const CrawlSummary: React.FC<CrawlSummaryProps> = ({ sessionId }) => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSummary();
  }, [sessionId]);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const summaryData = await apiService.getCrawlSummary(sessionId);
      setSummary(summaryData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch crawl summary');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const statusCodesData = Object.entries(summary.status_codes || {}).map(([code, count]) => ({
    name: `${code}`,
    value: count as number,
    fill: code.startsWith('2') ? '#4caf50' : code.startsWith('3') ? '#ff9800' : '#f44336'
  }));

  const issuesData = Object.entries(summary.issues_by_severity || {}).map(([severity, count]) => ({
    severity: severity.charAt(0).toUpperCase() + severity.slice(1),
    count: count as number,
    fill: severity === 'critical' ? '#f44336' : severity === 'high' ? '#ff9800' : severity === 'medium' ? '#2196f3' : '#4caf50'
  }));

  const totalIssues = Object.values(summary.issues_by_severity || {}).reduce((a: number, b: any) => a + b, 0);

  return (
    <Grid container spacing={3}>
      {/* Key Metrics */}
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" component="div" fontWeight="bold">
                  {summary.session.crawled_urls}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Pages Crawled
                </Typography>
              </Box>
              <PagesIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" component="div" fontWeight="bold">
                  {totalIssues}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Issues
                </Typography>
              </Box>
              <IssuesIcon sx={{ fontSize: 40, color: 'warning.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" component="div" fontWeight="bold">
                  {summary.avg_load_time.toFixed(2)}s
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Load Time
                </Typography>
              </Box>
              <SpeedIcon sx={{ fontSize: 40, color: 'info.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" component="div" fontWeight="bold">
                  {Math.round(summary.avg_word_count)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Word Count
                </Typography>
              </Box>
              <TrendIcon sx={{ fontSize: 40, color: 'success.main' }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Status Codes Chart */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              HTTP Status Codes
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusCodesData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusCodesData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Issues by Severity Chart */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Issues by Severity
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={issuesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="severity" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Crawl Configuration Summary */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Crawl Configuration
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Max URLs</Typography>
                <Typography variant="h6">{summary.session.config.max_urls}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Max Depth</Typography>
                <Typography variant="h6">{summary.session.config.max_depth}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Request Delay</Typography>
                <Typography variant="h6">{summary.session.config.delay}s</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">JavaScript Rendering</Typography>
                <Typography variant="h6">
                  {summary.session.config.render_javascript ? 'Enabled' : 'Disabled'}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default CrawlSummary;
