@echo off
echo Setting up SEO Analyzer with Docker...

REM Create project structure
mkdir seo-analyzer
cd seo-analyzer
mkdir backend frontend database nginx nginx\ssl

REM Create .env file
echo # Database Configuration > .env
echo POSTGRES_DB=seo_analyzer >> .env
echo POSTGRES_USER=seouser >> .env
echo POSTGRES_PASSWORD=seopassword123 >> .env
echo. >> .env
echo # Application Configuration >> .env
echo SECRET_KEY=your-super-secret-key-change-this >> .env
echo ALGORITHM=HS256 >> .env
echo ACCESS_TOKEN_EXPIRE_MINUTES=30 >> .env
echo. >> .env
echo # Environment >> .env
echo ENVIRONMENT=development >> .env
echo DEBUG=true >> .env

echo Project structure created!
echo Please add the Docker files and run: docker-compose up --build
pause
