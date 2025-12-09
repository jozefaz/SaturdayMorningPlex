# Use Python slim image for smaller size
FROM python:3.11-slim

# Set metadata labels for GitHub Container Registry and UnRAID
LABEL org.opencontainers.image.source="https://github.com/jozefaz/SaturdayMorningPlex"
LABEL org.opencontainers.image.description="Automated Plex playlist generator that creates Saturday morning cartoon-style weekly schedules with content rating filters and round-robin episode distribution"
LABEL org.opencontainers.image.licenses="MIT"
LABEL maintainer="jozefaz"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY plex_connection.py .
COPY playlist_generator.py .
COPY templates/ templates/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "60", "app:app"]
