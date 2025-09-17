#!/bin/bash
# Quick deployment script to update the GCP VM with latest code

set -e

echo "🚀 Deploying latest code to GCP VM..."

# VM details
VM_IP="34.28.161.37"
VM_USER="tejaswinrenugunta"  # Adjust if different
PROJECT_DIR="/home/$VM_USER/options-scanner"

# Create deployment commands
cat > /tmp/vm_deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "📥 Updating code on VM..."

# Navigate to project directory
cd /home/$(whoami)/options-scanner || {
    echo "❌ Project directory not found"
    exit 1
}

# Stop existing processes
echo "🛑 Stopping existing processes..."
sudo pkill -f gunicorn || echo "No gunicorn processes found"

# Update code
echo "📦 Pulling latest code..."
git stash || echo "No changes to stash"
git pull origin main

# Activate virtual environment
echo "🔧 Setting up environment..."
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Start the application
echo "🚀 Starting application..."
nohup gunicorn --bind 0.0.0.0:8080 --workers 5 --timeout 120 app:app > gunicorn.log 2>&1 &

# Wait for startup
sleep 5

# Check if app is running
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Application restarted successfully"
    echo "🌐 Testing API endpoint..."
    
    # Test the fixed endpoint
    curl -s "http://localhost:8080/api/stock/comprehensive/AAPL" | head -50
    
    echo ""
    echo "🎉 Deployment complete! Access at: http://34.28.161.37:8080"
else
    echo "❌ Failed to start application"
    echo "📋 Checking logs..."
    tail -20 gunicorn.log
    exit 1
fi
EOF

echo "📤 Copying deployment script to VM..."
scp /tmp/vm_deploy.sh $VM_USER@$VM_IP:/tmp/vm_deploy.sh

echo "🔧 Executing deployment on VM..."
ssh $VM_USER@$VM_IP 'chmod +x /tmp/vm_deploy.sh && /tmp/vm_deploy.sh'

echo "✅ Deployment completed!"
echo "🧪 Testing the fix..."

# Test the fixed API endpoint
echo "Testing stock detail API..."
curl -s "http://$VM_IP:8080/api/stock/comprehensive/LMND" | head -100

echo ""
echo "🎯 Stock detail pages should now work at: http://$VM_IP:8080/stock/LMND"
