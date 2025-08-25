#!/bin/bash

# Options Scanner Deployment Script for GCP VM
# This script pulls the latest code and restarts the application

set -e  # Exit on any error

echo "🚀 Starting Options Scanner deployment..."
echo "========================================"

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p logs
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$HOME/options-scanner"
VENV_PATH="$PROJECT_DIR/venv"
APP_PORT=8080

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory $PROJECT_DIR not found!"
    exit 1
fi

cd "$PROJECT_DIR"

# Stop any running processes on the port
print_status "Stopping any existing processes on port $APP_PORT..."
sudo pkill -f "gunicorn.*:$APP_PORT" || true
sudo pkill -f "python.*app.py" || true

# Wait a moment for processes to stop
sleep 2

# Pull latest code from GitHub
print_status "Pulling latest code from GitHub..."
git pull origin main

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at $VENV_PATH"
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install/update dependencies
print_status "Activating virtual environment and updating dependencies..."
source "$VENV_PATH/bin/activate"

# Install/update requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    print_status "Installing/updating Python packages..."
    pip install -r requirements.txt
fi

# Check if port 8080 is available, if not try port 80
print_status "Checking port availability..."
if netstat -tuln | grep -q ":$APP_PORT "; then
    print_warning "Port $APP_PORT is busy, trying port 80..."
    APP_PORT=80
    USE_SUDO="sudo"
else
    USE_SUDO=""
fi

# Start the application
print_status "Starting Options Scanner on port $APP_PORT..."

if [ "$APP_PORT" = "80" ]; then
    print_warning "Using sudo for port 80..."
    sudo "$VENV_PATH/bin/gunicorn" --bind 0.0.0.0:80 app:app --daemon --pid gunicorn.pid
else
    gunicorn --bind 0.0.0.0:$APP_PORT app:app --daemon --pid gunicorn.pid
fi

# Wait a moment and check if the app started successfully
sleep 3

if [ -f "gunicorn.pid" ]; then
    PID=$(cat gunicorn.pid)
    if ps -p $PID > /dev/null; then
        print_status "✅ Options Scanner started successfully!"
        print_status "🌐 Access your app at: http://$(curl -s ifconfig.me):$APP_PORT"
        print_status "📊 Process ID: $PID"
        
        # Show recent logs
        print_status "Recent application logs:"
        tail -n 10 /var/log/syslog | grep gunicorn || echo "No recent logs found"
    else
        print_error "Failed to start the application"
        exit 1
    fi
else
    print_error "Could not find PID file. Application may not have started correctly."
    exit 1
fi

print_status "🎉 Deployment completed successfully!"
echo ""
echo "Commands to manage your app:"
echo "  Stop:    sudo pkill -f gunicorn"
echo "  Restart: ./deploy.sh"
echo "  Logs:    tail -f /var/log/syslog | grep gunicorn"
