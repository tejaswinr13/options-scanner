#!/bin/bash
# Quick deployment update script for GCP VM

set -e

echo "🔄 Updating deployment on GCP VM..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VM_IP="34.28.161.37"
REPO_URL="https://github.com/tejaswinr13/options-scanner.git"

echo -e "${YELLOW}Step 1: Testing VM connectivity...${NC}"
if curl -s --connect-timeout 5 http://$VM_IP:8080 > /dev/null; then
    echo -e "${GREEN}✅ VM is accessible${NC}"
else
    echo "❌ VM not accessible, please check connection"
    exit 1
fi

echo -e "${YELLOW}Step 2: Creating deployment commands...${NC}"

# Create the deployment commands to run on the VM
cat > deploy_commands.sh << 'EOF'
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
EOF

echo -e "${GREEN}✅ Deployment script ready${NC}"
echo ""
echo "To deploy the updates, run this command:"
echo "scp deploy_commands.sh your-vm-user@$VM_IP:~ && ssh your-vm-user@$VM_IP 'chmod +x deploy_commands.sh && ./deploy_commands.sh'"
echo ""
echo "Or if you have gcloud configured:"
echo "gcloud compute scp deploy_commands.sh stock-dashboard-vm:~ --zone=us-central1-a"
echo "gcloud compute ssh stock-dashboard-vm --zone=us-central1-a --command='chmod +x deploy_commands.sh && ./deploy_commands.sh'"
