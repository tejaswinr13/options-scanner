# GCP VM Deployment Guide with HTTPS

## Prerequisites
- GCP account with billing enabled
- Domain name (for SSL certificate)
- Basic knowledge of Linux commands

## Step 1: Create GCP VM Instance

### 1.1 Create VM Instance
```bash
# Using gcloud CLI (or use GCP Console)
gcloud compute instances create stock-dashboard-vm \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=your-service-account@your-project.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=stock-dashboard-vm,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20231101,mode=rw,size=20,type=projects/your-project/zones/us-central1-a/diskTypes/pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --reservation-affinity=any
```

### 1.2 Configure Firewall Rules
```bash
# Allow HTTP traffic
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP traffic"

# Allow HTTPS traffic
gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS traffic"

# Allow custom port (optional, for testing)
gcloud compute firewall-rules create allow-8080 \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow port 8080"
```

## Step 2: Connect to VM and Setup Environment

### 2.1 SSH into VM
```bash
gcloud compute ssh stock-dashboard-vm --zone=us-central1-a
```

### 2.2 Update System and Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ and pip
sudo apt install python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx -y

# Install build tools for some Python packages
sudo apt install build-essential python3-dev -y
```

### 2.3 Clone and Setup Application
```bash
# Clone your repository (replace with your actual repo)
git clone https://github.com/yourusername/stock-dashboard.git
cd stock-dashboard

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn
```

## Step 3: Configure Application for Production

### 3.1 Update app.py for Production
```python
# Add to app.py
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
```

### 3.2 Create Gunicorn Configuration
```bash
# Create gunicorn.conf.py
cat > gunicorn.conf.py << 'EOF'
bind = "0.0.0.0:8080"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF
```

### 3.3 Create Systemd Service
```bash
sudo tee /etc/systemd/system/stock-dashboard.service > /dev/null << 'EOF'
[Unit]
Description=Stock Dashboard Flask App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/stock-dashboard
Environment="PATH=/home/ubuntu/stock-dashboard/venv/bin"
ExecStart=/home/ubuntu/stock-dashboard/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable stock-dashboard
sudo systemctl start stock-dashboard
sudo systemctl status stock-dashboard
```

## Step 4: Configure Nginx Reverse Proxy

### 4.1 Create Nginx Configuration
```bash
sudo tee /etc/nginx/sites-available/stock-dashboard > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static {
        alias /home/ubuntu/stock-dashboard/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/stock-dashboard /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## Step 5: Setup Domain and DNS

### 5.1 Point Domain to VM
1. Get your VM's external IP:
```bash
gcloud compute instances describe stock-dashboard-vm --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

2. In your domain registrar's DNS settings:
   - Create an A record pointing your domain to the VM's external IP
   - Create a CNAME record for www pointing to your domain

### 5.2 Reserve Static IP (Recommended)
```bash
# Reserve static IP
gcloud compute addresses create stock-dashboard-ip --region=us-central1

# Get the reserved IP
gcloud compute addresses describe stock-dashboard-ip --region=us-central1

# Assign to VM
gcloud compute instances delete-access-config stock-dashboard-vm --zone=us-central1-a --access-config-name="External NAT"
gcloud compute instances add-access-config stock-dashboard-vm --zone=us-central1-a --access-config-name="External NAT" --address=RESERVED_IP_ADDRESS
```

## Step 6: Setup HTTPS with Let's Encrypt

### 6.1 Install SSL Certificate
```bash
# Make sure your domain is pointing to the VM first!
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 6.2 Setup Auto-renewal
```bash
# Add to crontab
sudo crontab -e

# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Step 7: Security and Optimization

### 7.1 Configure UFW Firewall
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status
```

### 7.2 Setup Log Rotation
```bash
sudo tee /etc/logrotate.d/stock-dashboard > /dev/null << 'EOF'
/home/ubuntu/stock-dashboard/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload stock-dashboard
    endscript
}
EOF
```

### 7.3 Setup Monitoring
```bash
# Install htop for monitoring
sudo apt install htop -y

# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status ==="
systemctl status stock-dashboard --no-pager
echo "=== Nginx Status ==="
systemctl status nginx --no-pager
echo "=== Disk Usage ==="
df -h
echo "=== Memory Usage ==="
free -h
echo "=== Recent Logs ==="
journalctl -u stock-dashboard --no-pager -n 10
EOF

chmod +x monitor.sh
```

## Step 8: Deployment Script

### 8.1 Create Deployment Script
```bash
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Restart services
sudo systemctl restart stock-dashboard
sudo systemctl restart nginx

# Check status
sleep 5
sudo systemctl status stock-dashboard --no-pager
sudo systemctl status nginx --no-pager

echo "Deployment completed successfully!"
echo "Your app is available at: https://your-domain.com"
EOF

chmod +x deploy.sh
```

## Step 9: Environment Variables (Optional)

### 9.1 Setup Environment File
```bash
# Create environment file
cat > .env << 'EOF'
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
# Add any API keys or configuration
EOF

# Update systemd service to load environment
sudo sed -i '/Environment="PATH=/after a Environment="FLASK_ENV=production"' /etc/systemd/system/stock-dashboard.service
sudo systemctl daemon-reload
sudo systemctl restart stock-dashboard
```

## Troubleshooting

### Check Logs
```bash
# Application logs
journalctl -u stock-dashboard -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# System logs
dmesg | tail
```

### Common Issues
1. **Port 8080 blocked**: Check firewall rules
2. **Domain not resolving**: Verify DNS settings
3. **SSL certificate issues**: Ensure domain points to correct IP
4. **Application not starting**: Check Python dependencies and logs

## Final Steps
1. Test your application at `https://your-domain.com`
2. Verify SSL certificate is working
3. Test all functionality
4. Setup monitoring and backups
5. Document any custom configurations

## Estimated Costs
- VM (e2-medium): ~$25-30/month
- Static IP: ~$1.5/month
- SSL Certificate: Free (Let's Encrypt)
- Total: ~$27-32/month
