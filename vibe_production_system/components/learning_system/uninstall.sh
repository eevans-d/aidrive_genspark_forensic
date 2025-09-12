#!/bin/bash
# VIBE Learning System Uninstall Script

set -e

echo "🗑️ Uninstalling VIBE Continuous Learning System"
echo "=============================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Stop and disable service
echo "⏹️ Stopping service..."
systemctl stop vibe-learning.service || true
systemctl disable vibe-learning.service || true

# Remove systemd service file
echo "🗑️ Removing systemd service..."
rm -f /etc/systemd/system/vibe-learning.service
systemctl daemon-reload

echo "✅ VIBE Learning System uninstalled successfully!"
echo "ℹ️ Log files and data preserved in /vibe_production_system/components/learning_system/"
