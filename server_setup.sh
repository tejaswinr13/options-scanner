#!/bin/bash
# Server Setup Script - Run this on the GCP VM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Stock Dashboard on GCP VM${NC}"

# Check if domain is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Domain name required${NC}"
    echo "Usage: ./server_setup.sh your-domain.com"
    exit 1
fi

DOMAIN_NAME=$1
echo -e "${GREEN}Domain: $DOMAIN_NAME${NC}"

# Step 1: Update system
echo -e "${YELLOW}Step 1: Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing dependencies...${NC}"
sudo apt install python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx build-essential python3-dev htop -y

# Step 3: Clone repository (you'll need to update this with your actual repo)
echo -e "${YELLOW}Step 3: Setting up application...${NC}"
cd /home/ubuntu

# If you have a git repository, clone it here
# git clone https://github.com/yourusername/stock-dashboard.git
# cd stock-dashboard

# For now, we'll create the directory structure
mkdir -p stock-dashboard
cd stock-dashboard

# Create logs directory
mkdir -p logs

# You'll need to upload your files here or clone from git
echo -e "${YELLOW}Please upload your application files to /home/ubuntu/stock-dashboard${NC}"
echo -e "${YELLOW}Or clone from your git repository${NC}"

# Step 4: Create virtual environment
echo -e "${YELLOW}Step 4: Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Step 5: Install Python dependencies (when requirements.txt is available)
echo -e "${YELLOW}Step 5: Installing Python dependencies...${NC}"
# pip install -r requirements.txt
# For now, install basic dependencies
pip install flask gunicorn yfinance pandas numpy scikit-learn requests beautifulsoup4 lxml

# Step 6: Create systemd service
echo -e "${YELLOW}Step 6: Creating systemd service...${NC}"
sudo tee /etc/systemd/system/stock-dashboard.service > /dev/null << EOF
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
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Step 7: Configure Nginx
echo -e "${YELLOW}Step 7: Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/stock-dashboard > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Increase timeout for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /home/ubuntu/stock-dashboard/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/stock-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Step 8: Configure UFW Firewall
echo -e "${YELLOW}Step 8: Configuring firewall...${NC}"
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Step 9: Setup SSL Certificate (after DNS is configured)
echo -e "${YELLOW}Step 9: SSL Certificate setup...${NC}"
echo -e "${YELLOW}Make sure your domain $DOMAIN_NAME points to this server's IP before running SSL setup${NC}"
echo -e "${YELLOW}Run this command after DNS propagation:${NC}"
echo -e "${GREEN}sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME${NC}"

# Step 10: Setup auto-renewal for SSL
echo -e "${YELLOW}Step 10: Setting up SSL auto-renewal...${NC}"
(sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -

# Step 11: Create deployment script
echo -e "${YELLOW}Step 11: Creating deployment script...${NC}"
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting deployment..."

# Pull latest code (if using git)
# git pull origin main

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
EOF

chmod +x deploy.sh

# Step 12: Create monitoring script
echo -e "${YELLOW}Step 12: Creating monitoring script...${NC}"
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status ==="
systemctl status stock-dashboard --no-pager
echo ""
echo "=== Nginx Status ==="
systemctl status nginx --no-pager
echo ""
echo "=== Disk Usage ==="
df -h
echo ""
echo "=== Memory Usage ==="
free -h
echo ""
echo "=== Recent Application Logs ==="
journalctl -u stock-dashboard --no-pager -n 10
echo ""
echo "=== Recent Nginx Logs ==="
sudo tail -n 5 /var/log/nginx/error.log
EOF

chmod +x monitor.sh

# Step 13: Setup log rotation
echo -e "${YELLOW}Step 13: Setting up log rotation...${NC}"
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

echo -e "${GREEN}✅ Server setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Upload your application files to /home/ubuntu/stock-dashboard"
echo "2. Make sure requirements.txt, app.py, and gunicorn.conf.py are in place"
echo "3. Point your domain $DOMAIN_NAME to this server's IP address"
echo "4. Wait for DNS propagation (can take up to 24 hours)"
echo "5. Run SSL certificate setup:"
echo -e "   ${GREEN}sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME${NC}"
echo "6. Start the application:"
echo -e "   ${GREEN}sudo systemctl enable stock-dashboard${NC}"
echo -e "   ${GREEN}sudo systemctl start stock-dashboard${NC}"
echo ""
echo -e "${GREEN}Useful commands:${NC}"
echo "- Check app status: sudo systemctl status stock-dashboard"
echo "- View app logs: journalctl -u stock-dashboard -f"
echo "- Monitor system: ./monitor.sh"
echo "- Deploy updates: ./deploy.sh"
