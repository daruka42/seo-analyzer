-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Create enum types for better data integrity
CREATE TYPE crawl_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE issue_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE issue_category AS ENUM ('technical', 'content', 'performance', 'accessibility', 'mobile', 'security');
CREATE TYPE link_type AS ENUM ('internal', 'external');
CREATE TYPE queue_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');

-- Create initial tables if they don't exist
-- Note: These will be managed by Alembic in production

-- Performance indexes for common queries
CREATE INDEX IF NOT EXISTS idx_pages_url_gin ON pages USING gin(url gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_pages_crawl_session ON pages(crawl_session_id);
CREATE INDEX IF NOT EXISTS idx_pages_status_code ON pages(status_code);
CREATE INDEX IF NOT EXISTS idx_pages_created_at ON pages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_seo_issues_page ON seo_issues(page_id);
CREATE INDEX IF NOT EXISTS idx_seo_issues_severity ON seo_issues(severity);
CREATE INDEX IF NOT EXISTS idx_seo_issues_category ON seo_issues(category);
CREATE INDEX IF NOT EXISTS idx_seo_issues_type ON seo_issues(issue_type);

CREATE INDEX IF NOT EXISTS idx_crawl_sessions_project ON crawl_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_crawl_sessions_status ON crawl_sessions(status);
CREATE INDEX IF NOT EXISTS idx_crawl_sessions_created ON crawl_sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_projects_domain ON projects(domain);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_page_links_from ON page_links(from_page_id);
CREATE INDEX IF NOT EXISTS idx_page_links_to ON page_links(to_page_id);
CREATE INDEX IF NOT EXISTS idx_page_links_type ON page_links(link_type);

CREATE INDEX IF NOT EXISTS idx_crawl_queue_session ON crawl_queue(crawl_session_id);
CREATE INDEX IF NOT EXISTS idx_crawl_queue_status ON crawl_queue(status);
CREATE INDEX IF NOT EXISTS idx_crawl_queue_priority ON crawl_queue(priority DESC);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_pages_title_fts ON pages USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_pages_content_fts ON pages USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(meta_description, '')));

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_pages_session_status ON pages(crawl_session_id, status_code);
CREATE INDEX IF NOT EXISTS idx_issues_page_severity ON seo_issues(page_id, severity);

-- Create a function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;$$ language 'plpgsql';

-- Initial configuration data
INSERT INTO projects (id, name, domain, description, created_at, updated_at) 
VALUES (
    uuid_generate_v4(),
    'Demo Project',
    'example.com',
    'Demo project for testing SEO analysis',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT DO NOTHING;

-- Create a view for quick crawl statistics
CREATE OR REPLACE VIEW crawl_statistics AS
SELECT 
    cs.id as session_id,
    cs.project_id,
    cs.status,
    cs.started_at,
    cs.completed_at,
    COUNT(p.id) as total_pages,
    COUNT(CASE WHEN p.status_code >= 200 AND p.status_code < 300 THEN 1 END) as successful_pages,
    COUNT(CASE WHEN p.status_code >= 400 THEN 1 END) as error_pages,
    COUNT(si.id) as total_issues,
    COUNT(CASE WHEN si.severity = 'critical' THEN 1 END) as critical_issues,
    COUNT(CASE WHEN si.severity = 'high' THEN 1 END) as high_issues,
    AVG(p.load_time) as avg_load_time,
    AVG(p.word_count) as avg_word_count
FROM crawl_sessions cs
LEFT JOIN pages p ON cs.id = p.crawl_session_id
LEFT JOIN seo_issues si ON p.id = si.page_id
GROUP BY cs.id, cs.project_id, cs.status, cs.started_at, cs.completed_at;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO seouser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO seouser;
GRANT USAGE ON SCHEMA public TO seouser;