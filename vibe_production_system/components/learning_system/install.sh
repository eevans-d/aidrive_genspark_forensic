#!/bin/bash
# VIBE Learning System Installation Script

set -e

echo "🚀 Installing VIBE Continuous Learning System"
echo "============================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Create vibe user if it doesn't exist
if ! id "vibe" &>/dev/null; then
    echo "👤 Creating vibe user..."
    useradd -r -s /bin/false -d /vibe_production_system vibe
fi

# Set proper ownership
echo "🔐 Setting file permissions..."
chown -R vibe:vibe /vibe_production_system/components/learning_system
chmod +x /vibe_production_system/components/learning_system/learning_scheduler.py

# Create log directory
echo "📁 Creating log directory..."
mkdir -p /var/log
touch /var/log/vibe_learning.log
chown vibe:vibe /var/log/vibe_learning.log

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install schedule sqlite3 numpy pathlib

# Install systemd service
echo "⚙️ Installing systemd service..."
cp /vibe_production_system/components/learning_system/vibe-learning.service /etc/systemd/system/
systemctl daemon-reload

# Enable and start service
echo "🎯 Enabling and starting service..."
systemctl enable vibe-learning.service
systemctl start vibe-learning.service

# Check service status
echo "📊 Service status:"
systemctl status vibe-learning.service --no-pager

echo ""
echo "✅ VIBE Learning System installed successfully!"
echo "📋 Service commands:"
echo "  • Status: sudo systemctl status vibe-learning"
echo "  • Start:  sudo systemctl start vibe-learning"
echo "  • Stop:   sudo systemctl stop vibe-learning"
echo "  • Logs:   sudo journalctl -u vibe-learning -f"
echo "  • Log file: /var/log/vibe_learning.log"
echo ""
echo "🔄 Automated Schedule:"
echo "  • Daily feedback capture: 03:00"
echo "  • Weekly pattern analysis: Monday 04:00"
echo "  • Weekly model retraining: Saturday 02:00"
echo "  • Health checks: Every 6 hours"
