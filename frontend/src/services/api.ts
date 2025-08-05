import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Types
export interface Project {
  id: string;
  name: string;
  domain: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CrawlConfig {
  max_urls: number;
  max_depth: number;
  delay: number;
  render_javascript: boolean;
  respect_robots: boolean;
  follow_redirects: boolean;
  exclude_patterns: string[];
}

export interface CrawlSession {
  id: string;
  project_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  error_message?: string;
  crawled_urls: number;
  total_urls?: number;
  config: CrawlConfig;
}

export interface Page {
  id: string;
  crawl_session_id: string;
  url: string;
  title?: string;
  status_code?: number;
  load_time?: number;
  word_count?: number;
  created_at: string;
}

export interface SEOIssue {
  id: string;
  page_id: string;
  issue_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category?: string;
  description: string;
  recommendation?: string;
  impact_score: number;
  created_at: string;
}

// API Service
export const apiService = {
  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Projects
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get('/api/projects');
    return response.data.projects || [];
  },

  createProject: async (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<Project> => {
    const response = await apiClient.post('/api/projects', project);
    return response.data;
  },

  getProject: async (id: string): Promise<Project> => {
    const response = await apiClient.get(`/api/projects/${id}`);
    return response.data;
  },

  updateProject: async (id: string, project: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put(`/api/projects/${id}`, project);
    return response.data;
  },

  deleteProject: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/projects/${id}`);
  },

  // Crawl Sessions
  getCrawlSessions: async (projectId: string): Promise<CrawlSession[]> => {
    const response = await apiClient.get(`/api/projects/${projectId}/crawls`);
    return response.data;
  },

  getCrawlSession: async (sessionId: string): Promise<CrawlSession> => {
    const response = await apiClient.get(`/api/crawls/${sessionId}`);
    return response.data;
  },

  startCrawl: async (projectId: string, config: CrawlConfig): Promise<CrawlSession> => {
    const response = await apiClient.post(`/api/projects/${projectId}/crawls`, config);
    return response.data;
  },

  stopCrawl: async (sessionId: string): Promise<void> => {
    await apiClient.post(`/api/crawls/${sessionId}/stop`);
  },

  // Pages
  getSessionPages: async (sessionId: string, offset: number = 0, limit: number = 50): Promise<Page[]> => {
    const response = await apiClient.get(`/api/crawls/${sessionId}/pages`, {
      params: { offset, limit }
    });
    return response.data;
  },

  // Issues
  getSessionIssues: async (sessionId: string, params?: any): Promise<SEOIssue[]> => {
    const response = await apiClient.get(`/api/crawls/${sessionId}/issues`, { params });
    return response.data;
  },

  // Summary
  getCrawlSummary: async (sessionId: string): Promise<any> => {
    const response = await apiClient.get(`/api/crawls/${sessionId}/summary`);
    return response.data;
  },
};

export default apiService;
