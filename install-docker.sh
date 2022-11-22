#!/bin/bash

# helpers
function install_docker() {
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
}

function setup_docker_group() {
    sudo usermod -aG docker $USER
}

function post_install_docker() {
    # check if user is in docker group, otherwise add user to docker group
    groups | grep "\bdocker\b" || setup_docker_group
}

install_docker
post_install_docker
echo "docker installed"
