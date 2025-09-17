#!/bin/bash
set -e

echo "🔄 Updating code on VM..."

# Navigate to project directory
cd /home/$(whoami)/options-scanner || {
    echo "Project directory not found, cloning repository..."
    git clone https://github.com/tejaswinr13/options-scanner.git
    cd options-scanner
}

# Stop existing processes
echo "Stopping existing processes..."
sudo pkill -f gunicorn || echo "No gunicorn processes found"

# Stash any local changes and pull latest
echo "Updating code..."
git stash || echo "No changes to stash"
git pull origin main

# Activate virtual environment and install dependencies
echo "Setting up environment..."
source venv/bin/activate || {
    python3 -m venv venv
    source venv/bin/activate
}

# Install/update dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start the application
echo "Starting application..."
nohup gunicorn --bind 0.0.0.0:8080 --workers 5 --timeout 120 app:app > gunicorn.log 2>&1 &

# Wait a moment for startup
sleep 3

# Check if app is running
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Application started successfully"
    echo "🌐 Access at: http://34.28.161.37:8080"
else
    echo "❌ Failed to start application"
    echo "Checking logs..."
    tail -20 gunicorn.log
    exit 1
fi
