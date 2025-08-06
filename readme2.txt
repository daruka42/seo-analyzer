📋 Basic Usage Workflow
1. Create a Project
Bash
Run
# Using curl
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Website",
    "domain": "example.com",
    "description": "SEO analysis for my website"
  }'
2. Start a Crawl
Bash
Run
# Get project ID from previous response, then start crawl
curl -X POST "http://localhost:8000/api/crawls/{project_id}/start" \
  -H "Content-Type: application/json" \
  -d '{
    "max_urls": 100,
    "max_depth": 3,
    "render_javascript": true,
    "mobile_analysis": true,
    "screenshot_enabled": false
  }'
3. Monitor Progress
Bash
Run
# Check crawl status
curl "http://localhost:8000/api/crawls/{session_id}/status"

# Or use WebSocket for real-time updates
# Connect to: ws://localhost:8000/api/crawls/ws/{session_id}
4. View Results
Bash
Run
# Get crawl summary
curl "http://localhost:8000/api/crawls/{session_id}/summary"

# Get pages with issues
curl "http://localhost:8000/api/crawls/{session_id}/pages?has_issues=true"

# Get detailed analytics
curl "http://localhost:8000/api/crawls/{session_id}/analytics"
🔧 Development Commands
Backend Development
Bash
Run
# Access backend container
docker-compose exec backend bash

# Run tests
docker-compose exec backend python -m pytest

# Check logs
docker-compose logs -f backend

# Restart backend only
docker-compose restart backend
Frontend Development
Bash
Run
# Access frontend container
docker-compose exec frontend sh

# Install new packages
docker-compose exec frontend npm install package-name

# Restart frontend
docker-compose restart frontend
Database Operations
Bash
Run
# Access PostgreSQL
docker-compose exec postgres psql -U seouser -d seo_analyzer

# Backup database
docker-compose exec postgres pg_dump -U seouser seo_analyzer > backup.sql

# Restore database
docker-compose exec -T postgres psql -U seouser seo_analyzer < backup.sql
🛠️ Useful Commands
System Management
Bash
Run
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: This deletes all data)
docker-compose down -v

# View resource usage
docker stats

# Clean up unused Docker resources
docker system prune -a
Debugging
Bash
Run
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend

# Check service health
docker-compose exec backend curl http://localhost:8000/health
Scaling Services
Bash
Run
# Scale Celery workers
docker-compose up -d --scale celery-worker=3

# Scale with resource limits
docker-compose up -d --scale celery-worker=2
🔍 Troubleshooting
Common Issues
1. Services not starting:

Bash
Run
# Check Docker daemon
docker info

# Check port conflicts
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
2. Database connection issues:

Bash
Run
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "
from core.database import engine
print('Database connection:', engine.execute('SELECT 1').scalar())
"
3. Frontend not loading:

Bash
Run
# Check if backend is accessible
curl http://localhost:8000/health

# Check frontend logs
docker-compose logs frontend
4. Memory issues:

Bash
Run
# Check container resource usage
docker stats

# Increase Docker memory limits in Docker Desktop
# Or adjust resource limits in docker-compose.yml
📊 Production Deployment
For production deployment:

Environment Variables: Create .env files for sensitive data
SSL/TLS: Add reverse proxy (nginx/traefik) with SSL certificates
Monitoring: Set up proper logging and monitoring
Backups: Implement automated database backups
Scaling: Use Docker Swarm or Kubernetes for scaling
This setup provides a complete, production-ready SEO analysis platform with real-time crawling, comprehensive analysis, and modern web interface!