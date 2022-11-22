#!/bin/bash
USERNAME="$1"

# parse args
if [ $# -lt 1 ]; then
    echo 1>&2 "$0: need username as first arg"
    exit 1
fi

# create sudo user
useradd -m -s /bin/bash $USERNAME
usermod -aG sudo $USERNAME

# copy ssh keys from current user to that user
mkdir -p /home/$USERNAME/.ssh
cp $HOME/.ssh/authorized_keys /home/$USERNAME/.ssh/
chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh

# remove password authentication for that user (if a policy isn't already in place)
grep "^$USERNAME\s" /etc/sudoers
if [[ $? -ne 0 ]]; then
	echo "$USERNAME	ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
fi
