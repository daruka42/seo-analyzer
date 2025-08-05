# Stop all services
docker-compose down

# Remove old images to force rebuild
docker rmi seo-analyzer-frontend:latest
docker rmi seo-analyzer-backend:latest

# Build and start services
docker-compose up --build

# Or if you want to see logs more clearly:
docker-compose up --build frontend
