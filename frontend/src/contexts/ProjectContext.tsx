import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Project, apiService } from '../services/api';

interface ProjectContextType {
  projects: Project[];
  loading: boolean;
  error: string | null;
  selectedProject: Project | null;
  refreshProjects: () => Promise<void>;
  selectProject: (project: Project | null) => void;
  createProject: (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => Promise<Project>;
  updateProject: (id: string, project: Partial<Project>) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const useProjects = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProjects must be used within a ProjectProvider');
  }
  return context;
};

interface ProjectProviderProps {
  children: ReactNode;
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const refreshProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedProjects = await apiService.getProjects();
      setProjects(fetchedProjects);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch projects');
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectProject = (project: Project | null) => {
    setSelectedProject(project);
  };

  const createProject = async (projectData: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<Project> => {
    try {
      const newProject = await apiService.createProject(projectData);
      setProjects(prev => [...prev, newProject]);
      return newProject;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create project';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const updateProject = async (id: string, projectData: Partial<Project>): Promise<Project> => {
    try {
      const updatedProject = await apiService.updateProject(id, projectData);
      setProjects(prev => prev.map(p => p.id === id ? updatedProject : p));
      if (selectedProject?.id === id) {
        setSelectedProject(updatedProject);
      }
      return updatedProject;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update project';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const deleteProject = async (id: string): Promise<void> => {
    try {
      await apiService.deleteProject(id);
      setProjects(prev => prev.filter(p => p.id !== id));
      if (selectedProject?.id === id) {
        setSelectedProject(null);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to delete project';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  const value: ProjectContextType = {
    projects,
    loading,
    error,
    selectedProject,
    refreshProjects,
    selectProject,
    createProject,
    updateProject,
    deleteProject,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};
