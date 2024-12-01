#!/bin/bash

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
GIT_SERVICE=$(get_config_value "git" "service")
GIT_API_TOKEN=$(get_config_value "git" "api_token")
REPO_OWNER=$(get_config_value "git" "repo_owner")
REPO_NAME=$(get_config_value "git" "repo_name")
DOMAIN=$(get_config_value "server" "domain")
USER=$(get_config_value "server" "user")
PORT=$(get_config_value "server" "port")
ENABLE_IPV6=$(get_config_value "server" "enable_ipv6")
INSTALL_DIR=$(get_config_value "installation" "install_dir")



# Greeting
echo "Welcome to the CLI Magic Bootstraps setup script!"
echo "This script will install all necessary components and deploy your app."
echo "Press Enter to continue..."
read

# This script is intedned to be executed without interaction beyond this point; it will setup the environment for our CLI Magic Bootstrap app.

# Update and upgrade the system
echo Installing necessary tools and packages for cli-magic-bootstraps to work (1/3)
sudo apt update # && sudo apt upgrade -y

# Install Python and Git
echo Installing necessary tools and packages for cli-magic-bootstraps to work (2/3)
sudo apt install -y curl wget python3 python3-pip git

# Install required Python packages
echo Installing necessary tools and packages for cli-magic-bootstraps to work (3/3)
pip3 install fuzzywuzzy python-Levenshtein requests Flask gunicorn
echo && echo


# [!] IMPORTANT
# Don't forget you need to clone this repo to your own account, modify the necessary details for GitHub below, and the API details in the app's python file.
# After this, the following will install the app to the /usr/local/bin folder,  inside that folder will be cli-magic-bootstrap, and inside that, the app's files.
# It's best that you inspect all files and you are aware of what code is executed.


echo Cloning repo, be sure you made the necessary modifications or the script will fail here

# Clone your GitHub repository
git clone https://github.com/your_github_username/your_repo_name.git

# Ensure universal all lowercase name for dir, then cd into it
find . -iname "cli-magic-bootstrap" -exec mv {} cli-magic-bootstrap \;
cd cli-magic-bootstrap

# Create a systemd service file for the app
echo Creating magic_bootstraps service file
sudo bash -c 'cat <<EOL > /etc/systemd/system/magic_bootstraps.service
[Unit]
Description=Magic Bootstraps Service
After=network.target

[Service]
User=$USER
WorkingDirectory=/usr/local/bin/cli-magic-bootstrap
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL'

echo
echo Creating NGINX file for our app

# Create Nginx configuration
sudo bash -c "cat <<EOL > /etc/nginx/sites-available/$DOMAIN
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
    sudo bash -c "cat <<EOL >> /etc/nginx/sites-available/$DOMAIN
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
echo Script has finished. Try pointing your browser now to localhost:5000 or 127.0.0.1:5000
echo You will also need to add ports to your firewall policy before you can test public outside access
echo 
echo "ress any key to exit..."
read
exit