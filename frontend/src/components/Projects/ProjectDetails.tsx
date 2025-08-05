import React from 'react';
import {
  Box,
  Typography,
  Alert,
} from '@mui/material';

const ProjectDetails: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
        Project Details
      </Typography>
      
      <Alert severity="info">
        Project details page is under construction. This will show project information and crawl history.
      </Alert>
    </Box>
  );
};

export default ProjectDetails;
