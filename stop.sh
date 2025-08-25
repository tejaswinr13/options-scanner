#!/bin/bash

# Stop Options Scanner Script
# This script stops the running application

set -e

echo "🛑 Stopping Options Scanner..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop gunicorn processes
print_status "Stopping gunicorn processes..."
sudo pkill -f "gunicorn.*app:app" || true

# Stop any Python app processes
print_status "Stopping Python app processes..."
sudo pkill -f "python.*app.py" || true

# Remove PID file if it exists
if [ -f "gunicorn.pid" ]; then
    print_status "Removing PID file..."
    rm -f gunicorn.pid
fi

# Wait a moment
sleep 2

# Check if any processes are still running
if pgrep -f "gunicorn.*app:app" > /dev/null || pgrep -f "python.*app.py" > /dev/null; then
    print_error "Some processes may still be running. Use 'ps aux | grep -E \"(gunicorn|python.*app)\"' to check."
else
    print_status "✅ Options Scanner stopped successfully!"
fi
