#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [-y]"
    echo "  -y    Bypass confirmation prompt"
    exit 1
}

# Parse command-line options
while getopts ":y" opt; do
    case ${opt} in
        y )
            AUTO_CONFIRM=true
            ;;
        \? )
            usage
            ;;
    esac
done

# Function to read values from settings.conf
function get_config_value() {
    local section=$1
    local key=$2
    awk -F "=" -v section="$section" -v key="$key" '
    $0 ~ "\\["section"\\]" { in_section=1 }
    in_section && $1 ~ key { gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2; exit }
    ' settings.conf
}

# Load configuration from settings.conf
GIT_SERVICE=$(get_config_value "GIT Settings" "service")
GIT_API_TOKEN=$(get_config_value "GIT Settings" "api_token")
REPO_OWNER=$(get_config_value "GIT Settings" "repo_owner")
REPO_NAME=$(get_config_value "GIT Settings" "repo_name")
DOMAIN=$(get_config_value "Server Settings" "domain")
USER=$(get_config_value "Server Settings" "user")
PORT=$(get_config_value "Server Settings" "port")
ENABLE_IPV6=$(get_config_value "Server Settings" "enable_ipv6")
INSTALL_DIR=$(get_config_value "Installation Settings" "install_dir")

# Greeting
echo "Welcome to the CLI Magic Bootstraps setup script!"
echo "This script will install all necessary components and deploy your app."
echo "Press Enter to continue..."
read

# Simulate package installation
echo "Simulating package installation..."
sudo apt-get install -y curl wget python3 python3-pip git -s

# Confirmation prompt
if [ -z "$AUTO_CONFIRM" ]; then
    echo "The above packages will be installed."
    read -p "Do you want to proceed with the actual installation? (y/n): " choice
    case "$choice" in 
      y|Y ) echo "Proceeding with installation...";;
      n|N ) echo "Installation aborted."; exit 1;;
      * ) echo "Invalid choice. Installation aborted."; exit 1;;
    esac
fi

# Update and upgrade the system
echo "Installing necessary tools and packages for cli-magic-bootstraps to work (1/3)"
sudo apt update # && sudo apt upgrade -y

# Install Python and Git
echo "Installing necessary tools and packages for cli-magic-bootstraps to work (2/3)"
sudo apt install -y curl wget python3 python3-pip git

# Install required Python packages
echo "Installing necessary tools and packages for cli-magic-bootstraps to work (3/3)"
pip3 install fuzzywuzzy python-Levenshtein requests Flask gunicorn
echo && echo

# [!] IMPORTANT
# Don't forget you need to clone this repo to your own account, modify the necessary details for GitHub below, and the API details in the app's python file.
# After this, the following will install the app to the /usr/local/bin folder, inside that folder will be cli-magic-bootstrap, and inside that, the app's files.
# It's best that you inspect all files and you are aware of what code is executed.

echo "Cloning repo, be sure you made the necessary modifications or the script will fail here"

# In case we need to clean old installation
#rm -rf /home/USERNAME/cli-magic-bootstraps
#rm -rf /usr/local.bin/cli-magic-bootstraps

# Clone your GitHub repository
git clone https://github.com/$REPO_OWNER/$REPO_NAME.git

# Ensure universal all lowercase name for dir, then cd into it
find . -iname "cli-magic-bootstrap" -exec mv {} cli-magic-bootstrap \;
cd cli-magic-bootstrap

# Create a systemd service file for the app
echo "Creating magic_bootstraps service file"
rm -rf /etc/systemd/system/magic_bootstraps.service
sudo bash -c "cat <<EOL > /etc/systemd/system/magic_bootstraps.service
[Unit]
Description=Magic Bootstraps Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/gunicorn -w 4 -b 0.0.0.0:$PORT app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL"

echo
echo "Creating NGINX file for our app"

# Create Nginx configuration
sudo bash -c "cat <<EOL > /etc/nginx/config.d/$DOMAIN
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL"

# Enable IPv6 if specified
if [ "$ENABLE_IPV6" = true ]; then
    #sudo bash -c "cat <<EOL >> /etc/nginx/config.d/$DOMAIN
    sudo bash -c "cat <<EOL >> /etc/nginx/config.d/$DOMAIN
server {
    listen [::]:80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://[::1]:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL"
fi

# Enable the Nginx configuration
sudo ln -s /etc/nginx/config.d/$DOMAIN /etc/nginx/config.d
sudo nginx -t
sudo systemctl restart nginx

# Reload systemd and start the service
echo "Enabling magic_bootstraps.service"
sudo systemctl daemon-reload
sudo systemctl enable magic_bootstraps.service
sleep 1
sudo systemctl start magic_bootstraps.service

# Reload nginx
echo "Reloading nginx"
sudo systemctl restart nginx
echo
echo "Script has finished. Try pointing your browser to localhost:$PORT or 127.0.0.1:$PORT."
echo "You will also need to add ports to your firewall policy before you can test public outside access."
echo
echo "Next time, you can bypass this confirmation by running the script with the -y flag."
echo "Press any key to exit..."
read
exit
