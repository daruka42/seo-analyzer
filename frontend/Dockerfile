# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files first
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy all source files
COPY . .

# Expose port
EXPOSE 3000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["npm", "start"]
