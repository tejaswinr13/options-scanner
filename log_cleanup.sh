#!/bin/bash

# Options Scanner Log Cleanup Script
# Cleans up old log files and monitors disk usage

LOG_DIR="logs"
APP_LOG="$LOG_DIR/options_scanner.log"

echo "🧹 Options Scanner Log Cleanup"
echo "================================"

# Check if logs directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "✅ No logs directory found - nothing to clean"
    exit 0
fi

# Show current log sizes
echo "📊 Current log file sizes:"
if [ -f "$APP_LOG" ]; then
    ls -lh "$APP_LOG"
else
    echo "   No application log file found"
fi

# Show disk usage
echo ""
echo "💾 Disk usage:"
df -h . | head -2

# Clean up old rotated logs (keep last 5)
echo ""
echo "🗑️  Cleaning up old rotated logs..."
find "$LOG_DIR" -name "options_scanner.log.*" -type f | sort -V | head -n -5 | xargs -r rm -v

# Clean up system logs older than 30 days (if running as root/sudo)
if [ "$EUID" -eq 0 ]; then
    echo ""
    echo "🧽 Cleaning system logs older than 30 days..."
    find /var/log -name "*.log" -mtime +30 -type f -delete 2>/dev/null || true
    find /var/log -name "*.gz" -mtime +30 -type f -delete 2>/dev/null || true
fi

# Show final status
echo ""
echo "✅ Log cleanup completed!"
echo ""
echo "📈 Final disk usage:"
df -h . | head -2

# Show remaining log files
echo ""
echo "📁 Remaining log files:"
ls -lah "$LOG_DIR"/ 2>/dev/null || echo "   No log files found"
