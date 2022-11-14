#!/bin/bash

# stuff to setup throwing errors nicely
# https://intoli.com/blog/exit-on-errors-in-bash-scripts/
# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG

log_if_non_zero() {
    result=$?
    if [[ $result -ne 0 ]]; then
        echo "\"${last_command}\" command failed with exit code $result."
    else
        echo 'setup script successful'
    fi
}

# echo an error message before exiting
trap 'log_if_non_zero' EXIT

# parse args
if [ $# -lt 1 ]; then
    echo 1>&2 "$0: need hostname as first arg"
    exit 1
fi

hostname="$1"

# helpers
function install_docker() {
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
}

# actual script
apt-get update
apt-get install nginx -y
install_docker

cd # to $HOME
ls pipalhub || git clone https://github.com/pipalacademy/pipalhub
cd pipalhub
ln -sf $(pwd) /var/www/pipalhub

sed "s/server_name _;/server_name $hostname;/" etc/nginx/conf.d/lab.conf.sample > etc/nginx/conf.d/lab.conf
ln -sf "$(pwd)/etc/nginx/conf.d/lab.conf" /etc/nginx/conf.d/lab.conf

# dependencies that will likely be needed later (e.g. for jupyterhub services)
apt-get install python3-pip

# use certbot-nginx to setup ssl
apt-get install certbot python3-certbot-nginx -y
certbot --nginx -d $hostname --non-interactive --agree-tos --email anand@pipal.in

docker compose up -d
systemctl reload nginx

# set perms
chmod +x "$HOME"
chmod +x "$(pwd)"
chmod a+rwx "$(pwd)/tmp"
