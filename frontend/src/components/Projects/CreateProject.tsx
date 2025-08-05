import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  IconButton,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useProjects } from '../../contexts/ProjectContext';

const CreateProject: React.FC = () => {
  const navigate = useNavigate();
  const { createProject } = useProjects();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    description: '',
  });

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    // Clear error when user starts typing
    if (error) setError(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!formData.name.trim() || !formData.domain.trim()) {
      setError('Project name and domain are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const newProject = await createProject({
        name: formData.name.trim(),
        domain: formData.domain.trim(),
        description: formData.description.trim() || undefined,
        is_active: true,
      });
      
      navigate(`/project/${newProject.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={4}>
        <IconButton onClick={() => navigate(-1)} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Create New Project
        </Typography>
      </Box>

      <Card sx={{ maxWidth: 600 }}>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {error && (
                <Alert severity="error">{error}</Alert>
              )}

              <TextField
                label="Project Name"
                variant="outlined"
                fullWidth
                required
                value={formData.name}
                onChange={handleChange('name')}
                placeholder="e.g., Company Website Analysis"
                helperText="Give your project a descriptive name"
              />

              <TextField
                label="Domain"
                variant="outlined"
                fullWidth
                required
                value={formData.domain}
                onChange={handleChange('domain')}
                placeholder="e.g., example.com or https://example.com"
                helperText="Enter the domain or full URL to analyze"
              />

              <TextField
                label="Description"
                variant="outlined"
                fullWidth
                multiline
                rows={3}
                value={formData.description}
                onChange={handleChange('description')}
                placeholder="Optional description of the project..."
                helperText="Provide additional context about this project"
              />

              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate(-1)}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create Project'}
                </Button>
              </Box>
            </Box>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default CreateProject;
