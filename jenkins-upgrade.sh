#!/bin/bash
set -e

# Configuration
LOG_FILE="/var/log/jenkins_upgrade.log"
ADMIN_EMAIL="yash82206@gmail.com"
GMAIL_USER="technowebofficial01@gmail.com"
GMAIL_APP_PASSWORD="dxxaabikdjfdkplk"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a $LOG_FILE
}

# Function to send email via Gmail
send_email() {
    local subject="$1"
    local body="$2"
    
    curl --url "smtp://smtp.gmail.com:587" \
        --ssl-reqd \
        --mail-from "$GMAIL_USER" \
        --mail-rcpt "$ADMIN_EMAIL" \
        --user "$GMAIL_USER:$GMAIL_APP_PASSWORD" \
        --upload-file - <<EOF
Subject: $subject

$body
EOF
}

# Function to handle errors
handle_error() {
    local error_message="$1"
    log_message "ERROR: $error_message"
    send_email "Jenkins Upgrade Failed" "Error during Jenkins upgrade: $error_message\\n\\nCheck logs at $LOG_FILE for more details."
    exit 1
}

# Set error handler
trap '"handle_error \"Unexpected error occurred at line $LINENO\""' ERR

# Get current Jenkins version
log_message "Starting Jenkins upgrade process."
CURRENT_VERSION=$(sudo jenkins --version)
log_message "Current Jenkins version: $CURRENT_VERSION"

# Backup Jenkins configuration
BACKUP_DIR="/var/lib/jenkins/backup_$(date +%Y%m%d_%H%M%S)"
log_message "Creating backup directory at $BACKUP_DIR."
sudo mkdir -p $BACKUP_DIR
log_message "Backing up Jenkins configuration files to $BACKUP_DIR."
sudo cp -r /var/lib/jenkins/* $BACKUP_DIR/ || handle_error "Backup failed. Unable to copy Jenkins configuration files."

# Step 2: Download Jenkins repository key
log_message "Downloading Jenkins repository key from https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key."
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
    https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key || \
    handle_error "Failed to download Jenkins key."

# Step 3: Add Jenkins repository
log_message "Adding Jenkins repository to the system's package sources."
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
    https://pkg.jenkins.io/debian-stable binary/" | \
    sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null || \
    handle_error "Failed to add Jenkins repository."

# Step 4: Update package index
log_message "Updating the package index to include the new Jenkins repository."
sudo apt update || handle_error "Failed to update package index."

# Stop Jenkins service
log_message "Stopping Jenkins service to prepare for the upgrade."
sudo systemctl stop jenkins

# Wait for service to stop completely
log_message "Waiting for Jenkins service to stop completely."
sleep 10

# Step 5: Upgrade Jenkins
log_message "Upgrading Jenkins to the latest version."
sudo apt upgrade jenkins -y || handle_error "Failed to upgrade Jenkins."

# Step 6: Restart Jenkins service
log_message "Restarting Jenkins service after the upgrade."
sudo systemctl restart jenkins || handle_error "Failed to restart Jenkins service."

# Wait for Jenkins to start up
log_message "Waiting for Jenkins to start. This may take a few minutes."
MAX_WAIT=300
WAIT_COUNT=0
while ! curl -s http://localhost:8080 > /dev/null; do
    sleep 5
    WAIT_COUNT=$((WAIT_COUNT + 5))
    log_message "Checking if Jenkins is up... (Waited: $WAIT_COUNT seconds)"
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        handle_error "Jenkins failed to start within 5 minutes."
    fi
done

# Get new version
NEW_VERSION=$(sudo jenkins --version)
log_message "Upgrade completed successfully. New Jenkins version: $NEW_VERSION"

# Send success email
SUCCESS_MESSAGE="Jenkins upgrade completed successfully.

Previous version: $CURRENT_VERSION
New version: $NEW_VERSION

Backup location: $BACKUP_DIR
Log file: $LOG_FILE

All upgrade steps completed successfully:
- Backup of Jenkins configuration
- Repository key download
- Repository configuration
- Package index update
- Jenkins upgrade
 - Service restart"

send_email "Jenkins Upgrade Successful" "$SUCCESS_MESSAGE"
