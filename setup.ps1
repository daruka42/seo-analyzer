# SEO Analyzer Docker Setup for Windows
Write-Host "🚀 Setting up SEO Analyzer with Docker..." -ForegroundColor Green

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Create project structure
$projectName = "seo-analyzer"
New-Item -ItemType Directory -Force -Path $projectName
Set-Location $projectName

$directories = @("backend", "frontend", "database", "nginx", "nginx/ssl")
foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir
    Write-Host "✅ Created directory: $dir" -ForegroundColor Green
}

# Create .env file
$envContent = @"
# Database Configuration
POSTGRES_DB=seo_analyzer
POSTGRES_USER=seouser
POSTGRES_PASSWORD=seopassword123

# Application Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs (add your API keys)
AHREFS_API_KEY=
MAJESTIC_API_KEY=
SERP_API_KEY=

# Environment
ENVIRONMENT=development
DEBUG=true
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ Created .env file" -ForegroundColor Green

Write-Host "🎉 Project structure created successfully!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Add all the Docker files (docker-compose.yml, Dockerfiles, etc.)" -ForegroundColor White
Write-Host "2. Run: docker-compose up --build" -ForegroundColor White
Write-Host "3. Visit http://localhost for the frontend" -ForegroundColor White
Write-Host "4. Visit http://localhost:8000/docs for the API documentation" -ForegroundColor White
