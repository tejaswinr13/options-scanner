#!/bin/bash

# Deployment Health Check Script
# This script helps verify if your stock dashboard app is running correctly

echo "=== Stock Dashboard Deployment Health Check ==="
echo "Timestamp: $(date)"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on GCP VM
print_status "Checking environment..."
if curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/name > /dev/null 2>&1; then
    INSTANCE_NAME=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/name)
    EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
    print_success "Running on GCP VM: $INSTANCE_NAME"
    print_success "External IP: $EXTERNAL_IP"
else
    print_warning "Not running on GCP VM (running locally)"
    EXTERNAL_IP="localhost"
fi

echo

# Check if virtual environment exists
print_status "Checking virtual environment..."
if [ -d "venv" ]; then
    print_success "Virtual environment found"
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_error "Virtual environment not found"
fi

echo

# Check Python packages
print_status "Checking Python dependencies..."
REQUIRED_PACKAGES=("flask" "gunicorn" "yfinance" "pandas" "numpy" "requests" "scikit-learn")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if pip show "$package" > /dev/null 2>&1; then
        VERSION=$(pip show "$package" | grep Version | cut -d' ' -f2)
        print_success "$package ($VERSION) installed"
    else
        print_error "$package not installed"
    fi
done

echo

# Check if app processes are running
print_status "Checking running processes..."
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    GUNICORN_PIDS=$(pgrep -f "gunicorn.*app:app")
    print_success "Gunicorn processes running (PIDs: $GUNICORN_PIDS)"
    
    # Show process details
    echo "Process details:"
    ps aux | grep gunicorn | grep -v grep
else
    print_warning "Gunicorn processes not found"
fi

echo

# Check ports
print_status "Checking port availability..."
PORTS=(8000 80 443)

for port in "${PORTS[@]}"; do
    if netstat -tuln | grep ":$port " > /dev/null 2>&1; then
        print_success "Port $port is in use"
    else
        print_warning "Port $port is not in use"
    fi
done

echo

# Test HTTP endpoints
print_status "Testing HTTP endpoints..."

# Test main page
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/" | grep -q "200"; then
    print_success "Main page (/) responds with HTTP 200"
else
    print_error "Main page (/) not responding correctly"
fi

# Test dashboard
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/dashboard" | grep -q "200"; then
    print_success "Dashboard (/dashboard) responds with HTTP 200"
else
    print_error "Dashboard (/dashboard) not responding correctly"
fi

# Test API endpoint
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/ticker-prices" | grep -q "200"; then
    print_success "API endpoint (/api/ticker-prices) responds with HTTP 200"
else
    print_error "API endpoint (/api/ticker-prices) not responding correctly"
fi

echo

# Test external access (if on GCP)
if [ "$EXTERNAL_IP" != "localhost" ]; then
    print_status "Testing external access..."
    
    if curl -s -o /dev/null -w "%{http_code}" "http://$EXTERNAL_IP:8000/" | grep -q "200"; then
        print_success "External access working: http://$EXTERNAL_IP:8000/"
    else
        print_error "External access not working"
    fi
    
    # Test HTTPS if available
    if curl -s -o /dev/null -w "%{http_code}" "https://tradepluse.site/" | grep -q "200"; then
        print_success "HTTPS domain working: https://tradepluse.site/"
    else
        print_warning "HTTPS domain not responding (may still be setting up)"
    fi
fi

echo

# Check logs for errors
print_status "Checking recent logs for errors..."
if [ -f "nohup.out" ]; then
    ERROR_COUNT=$(tail -100 nohup.out | grep -i error | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        print_warning "Found $ERROR_COUNT error(s) in recent logs"
        echo "Recent errors:"
        tail -100 nohup.out | grep -i error | tail -5
    else
        print_success "No errors found in recent logs"
    fi
else
    print_warning "Log file (nohup.out) not found"
fi

echo

# System resource check
print_status "Checking system resources..."
echo "Memory usage:"
free -h
echo
echo "Disk usage:"
df -h
echo
echo "CPU load:"
uptime

echo
echo "=== Health Check Complete ==="

# Summary
echo
print_status "SUMMARY:"
if pgrep -f "gunicorn.*app:app" > /dev/null && curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/" | grep -q "200"; then
    print_success "✅ App appears to be running correctly!"
    echo
    echo "Access your app at:"
    echo "  Local: http://localhost:8000/"
    if [ "$EXTERNAL_IP" != "localhost" ]; then
        echo "  External: http://$EXTERNAL_IP:8000/"
        echo "  Domain: https://tradepluse.site/ (if DNS is configured)"
    fi
else
    print_error "❌ App may not be running correctly. Check the issues above."
fi
