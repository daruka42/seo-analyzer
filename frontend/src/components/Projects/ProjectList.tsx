import React from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useProjects } from '../../contexts/ProjectContext';

const ProjectList: React.FC = () => {
  const navigate = useNavigate();
  const { projects, loading, error } = useProjects();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          My Projects
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/create')}
        >
          Create Project
        </Button>
      </Box>

      {projects.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No projects yet
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Create your first project to start analyzing websites
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/create')}
            >
              Create Your First Project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <Card 
                sx={{ 
                  height: '100%', 
                  cursor: 'pointer',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    transition: 'transform 0.2s',
                    boxShadow: (theme) => theme.shadows[8],
                  }
                }}
                onClick={() => navigate(`/project/${project.id}`)}
              >
                <CardContent>
                  <Typography variant="h6" component="h2" gutterBottom>
                    {project.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {project.domain}
                  </Typography>
                  {project.description && (
                    <Typography variant="body2" color="text.secondary">
                      {project.description}
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                    Created: {new Date(project.created_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default ProjectList;
