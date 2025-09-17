#!/bin/bash
# GCP Deployment Script for Stock Dashboard

set -e

echo "🚀 Starting GCP deployment setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required variables are set
if [ -z "$DOMAIN_NAME" ]; then
    echo -e "${RED}Error: DOMAIN_NAME environment variable not set${NC}"
    echo "Usage: DOMAIN_NAME=your-domain.com ./deploy_gcp.sh"
    exit 1
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID environment variable not set${NC}"
    echo "Usage: PROJECT_ID=your-gcp-project ./deploy_gcp.sh"
    exit 1
fi

echo -e "${GREEN}Domain: $DOMAIN_NAME${NC}"
echo -e "${GREEN}Project: $PROJECT_ID${NC}"

# Step 1: Create VM Instance
echo -e "${YELLOW}Step 1: Creating GCP VM instance...${NC}"
gcloud compute instances create stock-dashboard-vm \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=stock-dashboard-vm,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20231101,mode=rw,size=20,type=projects/$PROJECT_ID/zones/us-central1-a/diskTypes/pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --reservation-affinity=any

# Step 2: Configure Firewall Rules
echo -e "${YELLOW}Step 2: Configuring firewall rules...${NC}"
gcloud compute firewall-rules create allow-http \
    --project=$PROJECT_ID \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP traffic" || echo "HTTP rule already exists"

gcloud compute firewall-rules create allow-https \
    --project=$PROJECT_ID \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS traffic" || echo "HTTPS rule already exists"

gcloud compute firewall-rules create allow-8080 \
    --project=$PROJECT_ID \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow port 8080" || echo "Port 8080 rule already exists"

# Step 3: Reserve Static IP
echo -e "${YELLOW}Step 3: Reserving static IP...${NC}"
gcloud compute addresses create stock-dashboard-ip \
    --project=$PROJECT_ID \
    --region=us-central1 || echo "Static IP already exists"

STATIC_IP=$(gcloud compute addresses describe stock-dashboard-ip \
    --project=$PROJECT_ID \
    --region=us-central1 \
    --format='get(address)')

echo -e "${GREEN}Static IP: $STATIC_IP${NC}"

# Step 4: Assign Static IP to VM
echo -e "${YELLOW}Step 4: Assigning static IP to VM...${NC}"
gcloud compute instances delete-access-config stock-dashboard-vm \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --access-config-name="External NAT" || echo "No existing access config"

gcloud compute instances add-access-config stock-dashboard-vm \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --access-config-name="External NAT" \
    --address=$STATIC_IP

echo -e "${GREEN}✅ GCP infrastructure setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Point your domain $DOMAIN_NAME to IP: $STATIC_IP"
echo "2. SSH into the VM: gcloud compute ssh stock-dashboard-vm --zone=us-central1-a"
echo "3. Run the server setup script on the VM"
echo ""
echo -e "${GREEN}VM External IP: $STATIC_IP${NC}"
echo -e "${GREEN}SSH Command: gcloud compute ssh stock-dashboard-vm --project=$PROJECT_ID --zone=us-central1-a${NC}"
