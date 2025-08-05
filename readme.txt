3. Start the Application
bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
4. Access the Application
After successful startup, access these URLs:

Frontend Application: http://localhost:3000
Backend API: http://localhost:8000
API Documentation: http://localhost:8000/docs
API Health Check: http://localhost:8000/health
📋 Detailed Setup Instructions
Environment Variables
Create a .env file in the backend directory:

env
# Database
DATABASE_URL=postgresql://seouser:seopassword123@postgres:5432/seo_analyzer

# Redis
REDIS_URL=redis://redis:6379

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=true

# Crawler Settings
CRAWLER_MAX_WORKERS=10
CRAWLER_REQUEST_DELAY=1.0
CRAWLER_TIMEOUT=30

# External APIs (optional)
AHREFS_API_KEY=your-ahrefs-key
MAJESTIC_API_KEY=your-majestic-key
SERP_API_KEY=your-serp-key
Project Structure
seo-analyzer/ ├── docker-compose.yml ├── README.md ├── backend/ │ ├── Dockerfile │ ├── requirements.txt │ ├── main.py │ ├── core/ │ │ ├── config.py │ │ ├── database.py │ │ └── celery.py │ ├── models/ │ │ └── database.py │ ├── schemas/ │ │ └── schemas.py │ ├── api/ │ │ ├── projects.py │ │ └── crawls.py │ ├── services/ │ │ ├── crawler.py │ │ ├── content_analyzer.py │ │ └── seo_analyzer.py │ └── tasks/ │ └── crawler.py ├── frontend/ │ ├── Dockerfile │ ├── package.json │ ├── public/ │ └── src/ │ ├── App.tsx │ ├── components/ │ ├── contexts/ │ ├── services/ │ └── utils/ └── docker/ └── init.sql
🛠️ Development Commands
Basic Operations
bash
# View logs from all services
docker-compose logs -f

# View logs from specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a specific service
docker-compose restart backend

# Rebuild and restart a service
docker-compose up -d --build backend

# Stop all services
docker-compose down

# Stop and remove all data (⚠️ This deletes everything!)
docker-compose down -v
Backend Operations
bash
# Execute commands in backend container
docker-compose exec backend bash

# Create database tables
docker-compose exec backend python -c "from models.database import Base; from core.database import engine; Base.metadata.create_all(bind=engine)"

# Run tests
docker-compose exec backend pytest

# Check API health
curl http://localhost:8000/health
Database Operations
bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U seouser -d seo_analyzer

# Backup database
docker-compose exec postgres pg_dump -U seouser seo_analyzer > backup.sql

# Restore database
docker-compose exec -T postgres psql -U seouser seo_analyzer < backup.sql

# View database logs
docker-compose logs postgres
Scaling Services
bash
# Scale Celery workers
docker-compose up --scale celery_worker=3

# Scale with specific service updates
docker-compose up -d --scale celery_worker=5 backend
🔧 Troubleshooting
Common Issues
1. Port Conflicts

bash
# Check what's using ports
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Stop conflicting services
sudo systemctl stop postgresql  # If PostgreSQL is running locally
2. Permission Issues

bash
# Fix Docker permissions
sudo chmod 666 /var/run/docker.sock

# Reset Docker
docker system prune -a
3. Services Not Starting

bash
# Check service health
docker-compose ps

# Rebuild everything
docker-compose down -v
docker-compose up --build

# Check specific service logs
docker-compose logs backend
4. Database Connection Issues

bash
# Reset database
docker-compose down
docker volume rm seo-analyzer_postgres_data
docker-compose up postgres
5. Frontend Build Issues

bash
# Clear npm cache
docker-compose exec frontend npm cache clean --force

# Rebuild frontend
docker-compose build --no-cache frontend
🌟 Features
Core Features
✅ Multi-language Support (Hungarian + English)
✅ Real-time Web Crawling with JavaScript rendering
✅ Comprehensive SEO Analysis
✅ Project Management interface
✅ Background Task Processing
✅ Interactive Dashboards
SEO Analysis Capabilities
Technical SEO: Title tags, meta descriptions, heading structure
Content Analysis: Keyword density, readability, language detection
Performance: Load times, optimization recommendations
Accessibility: Alt text, form labels, heading hierarchy
Social Media: Open Graph tags, meta properties
Hungarian-Specific: Character encoding, local business schemas
Hungarian Language Features
🇭🇺 Automatic Language Detection
🇭🇺 Hungarian Stop Words for keyword analysis
🇭🇺 Hungarian Character Support (áéíóöőúüű)
🇭🇺 Localized Error Messages
🇭🇺 Hungarian Readability Calculations
🇭🇺 Local Business Schema Detection
📊 Usage Guide
1. Create a Project
Open http://localhost:3000
Click "Create Project"
Enter project name and domain (e.g., example.hu)
Add optional description
2. Start a Crawl
Open your project
Click "Start New Crawl"
Configure crawl settings:
Max URLs to crawl
Crawl depth
Request delay
JavaScript rendering
Click "Start Crawl"
3. Monitor Progress
Real-time progress updates
Live statistics
Estimated time remaining
4. Analyze Results
Summary: Overview of issues and performance
Pages: Detailed page analysis
Issues: Categorized SEO problems
Configuration: Crawl settings used
🔒 Security Notes
Production Deployment
bash
# Change default passwords
export POSTGRES_PASSWORD=your-secure-password
export SECRET_KEY=your-super-secure-secret-key

# Use HTTPS
# Configure reverse proxy (nginx/apache)
# Set up SSL certificates
Environment Variables for Production
env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key
DATABASE_URL=postgresql://user:secure_password@host:5432/db
📈 Performance Optimization
Resource Allocation
yaml
# In docker-compose.yml, add resource limits
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
Scaling for Production
bash
# Horizontal scaling
docker-compose up --scale celery_worker=5 --scale backend=2

# Load balancing (add nginx/haproxy)
# Database connection pooling
# Redis clustering
🤝 Contributing
Fork the repository
Create a feature branch
Make your changes
Test thoroughly
Submit a pull request
📝 License
This project is licensed under the MIT License.

Need Help?

Check the logs: docker-compose logs -f
Visit API docs: http://localhost:8000/docs
Check health: http://localhost:8000/health
Happy SEO Analyzing! 🚀