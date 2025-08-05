import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Box,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { apiService, SEOIssue } from '../../services/api';

interface IssuesListProps {
  sessionId: string;
}

const IssuesList: React.FC<IssuesListProps> = ({ sessionId }) => {
  const [issues, setIssues] = useState<SEOIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    fetchIssues();
  }, [sessionId, severityFilter, categoryFilter]);

  const fetchIssues = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (severityFilter) params.severity = severityFilter;
      if (categoryFilter) params.category = categoryFilter;
      
      const issuesData = await apiService.getSessionIssues(sessionId, params);
      setIssues(issuesData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch issues');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'high':
        return <WarningIcon color="warning" />;
      case 'medium':
        return <InfoIcon color="info" />;
      case 'low':
        return <CheckIcon color="success" />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const filteredIssues = issues.filter(issue =>
    issue.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    issue.issue_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const paginatedIssues = filteredIssues.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

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

  return (
    <Card>
      <CardContent>
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            SEO Issues
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search issues..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Severity</InputLabel>
                <Select
                  value={severityFilter}
                  label="Severity"
                  onChange={(e) => setSeverityFilter(e.target.value)}
                >
                  <MenuItem value="">All Severities</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Category</InputLabel>
                <Select
                  value={categoryFilter}
                  label="Category"
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <MenuItem value="">All Categories</MenuItem>
                  <MenuItem value="technical">Technical</MenuItem>
                  <MenuItem value="content">Content</MenuItem>
                  <MenuItem value="performance">Performance</MenuItem>
                  <MenuItem value="accessibility">Accessibility</MenuItem>
                  <MenuItem value="social">Social</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Box>

        {paginatedIssues.length === 0 ? (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
            No issues found matching your criteria.
          </Typography>
        ) : (
          <Box>
            {paginatedIssues.map((issue) => (
              <Accordion key={issue.id}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" width="100%" mr={2}>
                    <Box mr={2}>
                      {getSeverityIcon(issue.severity)}
                    </Box>
                    <Box flexGrow={1}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {issue.description}
                      </Typography>
                      <Box display="flex" gap={1} mt={1}>
                        <Chip
                          label={issue.severity.charAt(0).toUpperCase() + issue.severity.slice(1)}
                          color={getSeverityColor(issue.severity) as any}
                          size="small"
                        />
                        {issue.category && (
                          <Chip
                            label={issue.category.charAt(0).toUpperCase() + issue.category.slice(1)}
                            variant="outlined"
                            size="small"
                          />
                        )}
                        <Chip
                          label={`Impact: ${issue.impact_score}/100`}
                          variant="outlined"
                          size="small"
                        />
                      </Box>
                    </Box>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        Issue Type
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {issue.issue_type.replace(/_/g, ' ').toUpperCase()}
                      </Typography>
                      
                      <Typography variant="subtitle2" gutterBottom>
                        Description
                      </Typography>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {issue.description}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      {issue.recommendation && (
                        <>
                          <Typography variant="subtitle2" gutterBottom>
                            Recommendation
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {issue.recommendation}
                          </Typography>
                        </>
                      )}
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}

            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={filteredIssues.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default IssuesList;
