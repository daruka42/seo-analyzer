import React from 'react';
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import {
  Pages as PagesIcon,
  BugReport as IssuesIcon,
  Speed as SpeedIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { ProjectStats } from '../../services/api';

interface ProjectStatsCardsProps {
  stats: ProjectStats;
}

const ProjectStatsCards: React.FC<ProjectStatsCardsProps> = ({ stats }) => {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const statCards = [
    {
      title: 'Total Pages',
      value: stats.total_pages.toLocaleString(),
      icon: <PagesIcon sx={{ fontSize: 40 }} />,
      color: 'primary.main',
    },
    {
      title: 'Total Issues',
      value: (stats.critical_issues + stats.high_issues + stats.medium_issues + stats.low_issues).toLocaleString(),
      icon: <IssuesIcon sx={{ fontSize: 40 }} />,
      color: 'warning.main',
    },
    {
      title: 'Avg Load Time',
      value: stats.avg_load_time > 0 ? `${stats.avg_load_time.toFixed(2)}s` : 'N/A',
      icon: <SpeedIcon sx={{ fontSize: 40 }} />,
      color: 'info.main',
    },
    {
      title: 'Last Crawl',
      value: formatDate(stats.last_crawl),
      icon: <ScheduleIcon sx={{ fontSize: 40 }} />,
      color: 'success.main',
    },
  ];

  return (
    <Grid container spacing={3}>
      {statCards.map((card, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" component="div" fontWeight="bold">
                    {card.value}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {card.title}
                  </Typography>
                </Box>
                <Box sx={{ color: card.color }}>
                  {card.icon}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default ProjectStatsCards;
