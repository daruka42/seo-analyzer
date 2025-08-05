import React from 'react';
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
  Chip,
  Button,
  Box,
} from '@mui/material';
import { Launch as LaunchIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { CrawlSession } from '../../services/api';

interface RecentCrawlsListProps {
  crawls: CrawlSession[];
}

const RecentCrawlsList: React.FC<RecentCrawlsListProps> = ({ crawls }) => {
  const navigate = useNavigate();

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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const calculateDuration = (startDate: string, endDate?: string | null) => {
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffSecs = Math.floor((diffMs % 60000) / 1000);
    
    if (diffMins > 0) {
      return `${diffMins}m ${diffSecs}s`;
    }
    return `${diffSecs}s`;
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">
            Recent Crawls
          </Typography>
        </Box>

        {crawls.length === 0 ? (
          <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
            No crawls yet. Start your first crawl to see results here.
          </Typography>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Pages</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {crawls.map((crawl) => (
                  <TableRow key={crawl.id}>
                    <TableCell>
                      <Chip
                        label={crawl.status.charAt(0).toUpperCase() + crawl.status.slice(1)}
                        color={getStatusColor(crawl.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {formatDate(crawl.started_at)}
                    </TableCell>
                    <TableCell>
                      {crawl.status === 'running' 
                        ? 'Running...' 
                        : calculateDuration(crawl.started_at, crawl.completed_at)
                      }
                    </TableCell>
                    <TableCell>
                      {crawl.crawled_urls} / {crawl.total_urls || 'Unknown'}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<LaunchIcon />}
                        onClick={() => navigate(`/crawl/${crawl.id}`)}
                      >
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentCrawlsList;
