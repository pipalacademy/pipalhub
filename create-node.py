# Use digitalocean API to create a new node and setup
# Requires python-digitalocean to be installed
# python3 -m pip install python-digitalocean

import argparse
import os
import time

import digitalocean


# defaults

REGION = "blr1"
SIZES = {
    "small": "s-1vcpu-1gb",
    "medium": "s-1vcpu-2gb",
    "large": "s-2vcpu-2gb",
}
IMAGE = "ubuntu-22-04-x64"
BASE_DOMAIN = "pipal.in"

if not os.getenv("DIGITALOCEAN_TOKEN"):
    raise Exception("DIGITALOCEAN_TOKEN not set")

DIGITALOCEAN_TOKEN = os.getenv("DIGITALOCEAN_TOKEN")

def create_droplet(name, size, region, image):
    manager = digitalocean.Manager(token=DIGITALOCEAN_TOKEN)
    droplet = digitalocean.Droplet(
        token=DIGITALOCEAN_TOKEN,
        name=name,
        region=REGION,
        image=IMAGE,
        size_slug=SIZES[size],
        ssh_keys=manager.get_all_sshkeys(),
        backups=False,
    )
    droplet.create()
    action = droplet.get_actions()[0]
    action.wait()
    droplet.load()
    return droplet


def set_dns_record(hostname, ip):
    domain = digitalocean.Domain(token=DIGITALOCEAN_TOKEN, name=BASE_DOMAIN)
    for record in domain.get_records():
        if record.name == hostname:
            record.data = ip
            record.save()
            return record
    else:
        record = domain.create_new_domain_record(
            type="A",
            name=hostname,
            data=ip,
            ttl="300"
        )
        return digitalocean.Record.get_object(domain.token, domain.name, record["domain_record"]["id"])

def get_droplet(name):
    manager = digitalocean.Manager(token=DIGITALOCEAN_TOKEN)
    for droplet in manager.get_all_droplets():
        if droplet.name == name:
            return droplet
    return None

def system(cmd):
    print("running cmd:", cmd)
    return os.system(cmd)

def wait_for_ip_address(droplet, timeout=60):
    print("waiting for ip address to load")
    step = 5
    while timeout > 0:
        if droplet.ip_address:
            return
        time.sleep(step)
        timeout -= step
        droplet.load()
    raise Exception("timed out waiting for ip address")

def wait_for_ssh(droplet, timeout=60):
    print("waiting for ssh on droplet")
    time.sleep(timeout)

def log_droplet_created(droplet):
    print("Droplet created.")
    print("Name\t\t:", droplet.name)
    print("Size\t\t:", f"{droplet.memory}MB, {droplet.vcpus}vCPU ({droplet.size_slug})")
    print("IP\t\t:", droplet.ip_address)

def log_dns_record_set(record):
    print("DNS record set.")
    print("Name\t\t:", record.name)
    print("Type\t\t:", record.type)
    print("Data\t\t:", record.data)

def run_script(ip_address, local_path, user="root", args=""):
    # scp $local_path to the node and run it
    system(f"scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p '{local_path}' {user}@{ip_address}:/tmp/script.sh")
    system(f"ssh -o StrictHostKeyChecking=no {user}@{ip_address} /tmp/script.sh {args}")

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--name", help="name of the node", required=True)
    p.add_argument("--size", help="size of the node", required=True)
    p.add_argument("--hostname", help="hostname of the node without the domain", required=True)
    return p.parse_args()

def main():
    args = parse_args()
    name, hostname, size = args.name, args.hostname, args.size

    # create droplet with given params
    droplet = create_droplet(name, size, REGION, IMAGE)
    log_droplet_created(droplet)
    wait_for_ip_address(droplet, timeout=60)
    record = set_dns_record(hostname, droplet.ip_address)
    log_dns_record_set(record)
    wait_for_ssh(droplet, timeout=60)
    run_script(
        droplet.ip_address, local_path="setup-node.sh",
        user="root", args=f"{hostname}.{BASE_DOMAIN}")


if __name__ == "__main__":
    main()
