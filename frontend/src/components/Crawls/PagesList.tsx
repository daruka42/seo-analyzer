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
  Button,
  Box,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Launch as LaunchIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService, Page } from '../../services/api';

interface PagesListProps {
  sessionId: string;
}

const PagesList: React.FC<PagesListProps> = ({ sessionId }) => {
  const navigate = useNavigate();
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchPages();
  }, [sessionId, page, rowsPerPage]);

  const fetchPages = async () => {
    try {
      setLoading(true);
      const pagesData = await apiService.getSessionPages(
        sessionId,
        page * rowsPerPage,
        rowsPerPage
      );
      setPages(pagesData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch pages');
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

  const getStatusColor = (statusCode?: number) => {
    if (!statusCode) return 'default';
    if (statusCode >= 200 && statusCode < 300) return 'success';
    if (statusCode >= 300 && statusCode < 400) return 'warning';
    return 'error';
  };

  const filteredPages = pages.filter(page =>
    page.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (page.title && page.title.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading && pages.length === 0) {
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
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">Crawled Pages</Typography>
          <TextField
            size="small"
            placeholder="Search pages..."
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
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>URL</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Load Time</TableCell>
                <TableCell>Word Count</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredPages.map((pageData) => (
                <TableRow key={pageData.id}>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {pageData.url}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {pageData.title || 'No title'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={pageData.status_code || 'Unknown'}
                      color={getStatusColor(pageData.status_code)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {pageData.load_time ? `${pageData.load_time.toFixed(2)}s` : 'N/A'}
                  </TableCell>
                  <TableCell>
                    {pageData.word_count || 'N/A'}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      startIcon={<LaunchIcon />}
                      onClick={() => navigate(`/page/${pageData.id}`)}
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={pages.length} // Note: This should be total count from API
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </CardContent>
    </Card>
  );
};

export default PagesList;
