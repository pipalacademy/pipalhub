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

# actual script
sudo apt-get update
sudo apt-get install nginx -y

cd # to $HOME
ls pipalhub || git clone https://github.com/pipalacademy/pipalhub
cd pipalhub
sudo ln -sf $(pwd) /var/www/pipalhub

sed "s/server_name _;/server_name $hostname;/" etc/nginx/conf.d/lab.conf.sample > etc/nginx/conf.d/lab.conf
sudo ln -sf "$(pwd)/etc/nginx/conf.d/lab.conf" /etc/nginx/conf.d/lab.conf

# dependencies that will likely be needed later (e.g. for jupyterhub services)
sudo apt-get install -y python3-pip
python3 -m pip install --upgrade requests

# use certbot-nginx to setup ssl
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d $hostname --non-interactive --agree-tos --email anand@pipal.in

docker compose up -d
sudo systemctl reload nginx

# set perms
chmod +x "$HOME"
chmod +x "$(pwd)"
chmod a+rwx "$(pwd)/tmp"
