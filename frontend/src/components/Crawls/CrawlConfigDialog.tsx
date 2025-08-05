import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Grid,
  Typography,
  Box,
  Chip,
  IconButton,
  Divider,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { CrawlConfig } from '../../services/api';

interface CrawlConfigDialogProps {
  open: boolean;
  onClose: () => void;
  onStart: (config: CrawlConfig) => void;
  loading: boolean;
}

const CrawlConfigDialog: React.FC<CrawlConfigDialogProps> = ({
  open,
  onClose,
  onStart,
  loading,
}) => {
  const [config, setConfig] = useState<CrawlConfig>({
    max_urls: 100,
    max_depth: 3,
    delay: 1.0,
    render_javascript: true,
    respect_robots: true,
    follow_redirects: true,
    exclude_patterns: [],
  });

  const [newPattern, setNewPattern] = useState('');

  const handleChange = (field: keyof CrawlConfig, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleAddPattern = () => {
    if (newPattern.trim() && !config.exclude_patterns.includes(newPattern.trim())) {
      setConfig(prev => ({
        ...prev,
        exclude_patterns: [...prev.exclude_patterns, newPattern.trim()],
      }));
      setNewPattern('');
    }
  };

  const handleRemovePattern = (pattern: string) => {
    setConfig(prev => ({
      ...prev,
      exclude_patterns: prev.exclude_patterns.filter(p => p !== pattern),
    }));
  };

  const handleSubmit = () => {
    onStart(config);
  };

  const presetConfigs = [
    {
      name: 'Quick Scan',
      config: { ...config, max_urls: 50, max_depth: 2, delay: 0.5 },
    },
    {
      name: 'Standard Scan',
      config: { ...config, max_urls: 200, max_depth: 3, delay: 1.0 },
    },
    {
      name: 'Deep Scan',
      config: { ...config, max_urls: 1000, max_depth: 5, delay: 1.5 },
    },
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Configure Website Crawl</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {/* Preset Configurations */}
          <Typography variant="h6" gutterBottom>
            Quick Presets
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {presetConfigs.map((preset) => (
              <Grid item key={preset.name}>
                <Button
                  variant="outlined"
                  onClick={() => setConfig(preset.config)}
                >
                  {preset.name}
                </Button>
              </Grid>
            ))}
          </Grid>

          <Divider sx={{ mb: 3 }} />

          {/* Custom Configuration */}
          <Typography variant="h6" gutterBottom>
            Custom Configuration
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Maximum URLs"
                type="number"
                value={config.max_urls}
                onChange={(e) => handleChange('max_urls', parseInt(e.target.value))}
                inputProps={{ min: 1, max: 10000 }}
                helperText="Maximum number of pages to crawl"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Maximum Depth"
                type="number"
                value={config.max_depth}
                onChange={(e) => handleChange('max_depth', parseInt(e.target.value))}
                inputProps={{ min: 1, max: 10 }}
                helperText="How deep to follow links"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Delay Between Requests (seconds)"
                type="number"
                value={config.delay}
                onChange={(e) => handleChange('delay', parseFloat(e.target.value))}
                inputProps={{ min: 0.1, max: 10, step: 0.1 }}
                helperText="Delay to be respectful to the server"
              />
            </Grid>
          </Grid>

          {/* Advanced Options */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Advanced Options
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.render_javascript}
                      onChange={(e) => handleChange('render_javascript', e.target.checked)}
                    />
                  }
                  label="Render JavaScript"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.respect_robots}
                      onChange={(e) => handleChange('respect_robots', e.target.checked)}
                    />
                  }
                  label="Respect robots.txt"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.follow_redirects}
                      onChange={(e) => handleChange('follow_redirects', e.target.checked)}
                    />
                  }
                  label="Follow Redirects"
                />
              </Grid>
            </Grid>
          </Box>

          {/* Exclude Patterns */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Exclude URL Patterns
            </Typography>
            <Box display="flex" gap={2} mb={2}>
              <TextField
                fullWidth
                label="URL pattern to exclude"
                value={newPattern}
                onChange={(e) => setNewPattern(e.target.value)}
                placeholder="e.g., /admin/, .pdf, ?utm_"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddPattern();
                  }
                }}
              />
              <Button
                variant="outlined"
                onClick={handleAddPattern}
                startIcon={<AddIcon />}
              >
                Add
              </Button>
            </Box>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {config.exclude_patterns.map((pattern, index) => (
                <Chip
                  key={index}
                  label={pattern}
                  onDelete={() => handleRemovePattern(pattern)}
                  deleteIcon={<DeleteIcon />}
                />
              ))}
            </Box>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
        >
          {loading ? 'Starting...' : 'Start Crawl'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CrawlConfigDialog;
