FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r seoapp && useradd -r -g seoapp seoapp

# Install system dependencies including language support
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    gnupg \
    locales \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Configure Hungarian locale
RUN sed -i '/hu_HU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG=hu_HU.UTF-8 \
    LANGUAGE=hu_HU:hu \
    LC_ALL=hu_HU.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Node.js (for Playwright)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers (as root, then change ownership)
RUN playwright install --with-deps chromium

# Install spaCy models for both Hungarian and English
RUN python -m spacy download hu_core_news_sm || echo "Hungarian model not available, using fallback"
RUN python -m spacy download en_core_web_sm

# Create directories for data with proper permissions
RUN mkdir -p /app/data /app/logs /app/screenshots /app/exports \
    && chown -R seoapp:seoapp /app

# Copy application code
COPY --chown=seoapp:seoapp . .

# Switch to non-root user
USER seoapp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]