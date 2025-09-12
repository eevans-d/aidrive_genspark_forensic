# Dockerfile for Backup Automation Service
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gzip \
    tar \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backup_automation/requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create backup user
RUN useradd --create-home --shell /bin/bash backup

# Copy backup scripts
COPY backup_automation/ /app/
RUN chmod +x /app/backup_manager.py

# Create directories
RUN mkdir -p /var/log /etc/retail-backup /tmp/backups \
    && chown -R backup:backup /app /var/log /tmp/backups

# Switch to backup user
USER backup

# Setup cron job
COPY backup_automation/crontab /etc/cron.d/retail-backup
RUN chmod 0644 /etc/cron.d/retail-backup

# Default command
CMD ["python3", "/app/backup_manager.py", "schedule"]
