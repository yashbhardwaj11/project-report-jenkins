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

# Function to perform rollback
perform_rollback() {
    local error_message="$1"
    local backup_dir="$2"
    
    log_message "Starting rollback process due to: $error_message"
    
    # Stop Jenkins service
    log_message "Stopping Jenkins service for rollback"
    sudo systemctl stop jenkins || true
    
    # Wait for service to stop
    sleep 10
    
    # Restore from backup
    log_message "Restoring Jenkins files from backup: $backup_dir"
    if sudo rsync -av --delete "$backup_dir/" /var/lib/jenkins/; then
        log_message "Backup restoration completed"
        
        # Start Jenkins service
        log_message "Starting Jenkins service after rollback"
        sudo systemctl start jenkins
        
        # Wait for Jenkins to start
        local rollback_wait=0
        while ! curl -s http://localhost:8080 > /dev/null; do
            sleep 5
            rollback_wait=$((rollback_wait + 5))
            if [ $rollback_wait -ge 300 ]; then
                log_message "CRITICAL: Jenkins failed to start after rollback"
                send_email "Jenkins Rollback Failed" "Critical error: Jenkins failed to start after rollback attempt.\n\nOriginal error: $error_message\n\nManual intervention required."
                exit 2
            fi
        done
        
        log_message "Rollback completed successfully"
        send_email "Jenkins Rollback Completed" "Jenkins upgrade failed and system was rolled back to previous version.\n\nError: $error_message\n\nCheck logs at $LOG_FILE for more details."
    else
        log_message "CRITICAL: Rollback failed - unable to restore from backup"
        send_email "Jenkins Rollback Failed" "Critical error: Unable to restore Jenkins from backup.\n\nOriginal error: $error_message\n\nManual intervention required."
        exit 2
    fi
    exit 1
}

# Function to handle errors
handle_error() {
    local error_message="$1"
    log_message "ERROR: $error_message"
    
    if [ -n "$BACKUP_DIR" ]; then
        perform_rollback "$error_message" "$BACKUP_DIR"
    else
        send_email "Jenkins Upgrade Failed" "Error during Jenkins upgrade (before backup was created): $error_message\n\nCheck logs at $LOG_FILE for more details."
        exit 1
    fi
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
# Use rsync to copy files, excluding the backup directory
if sudo rsync -av --exclude='backup_*' /var/lib/jenkins/ $BACKUP_DIR/; then
    log_message "Backup completed successfully."
else
    handle_error "Backup failed. Unable to copy Jenkins configuration files."
fi

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
sudo systemctl stop jenkins || handle_error "Failed to stop Jenkins service."

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
send_email "Jenkins Upgrade Successful" "Jenkins has been upgraded successfully from version $CURRENT_VERSION to version $NEW_VERSION.\n\nCheck logs at $LOG_FILE for more details."
log_message "Jenkins upgrade process completed."
