-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create initial user (optional)
-- INSERT INTO users (id, email, hashed_password, is_active) 
-- VALUES (uuid_generate_v4(), 'admin@example.com', '$2b$12$...', true);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_pages_url ON pages USING gin(url gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_pages_session_id ON pages(session_id);
CREATE INDEX IF NOT EXISTS idx_seo_issues_page_id ON seo_issues(page_id);
CREATE INDEX IF NOT EXISTS idx_crawl_sessions_project_id ON crawl_sessions(project_id);
