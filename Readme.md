[PA]: https://pipal.in/
[ipytail]: https://github.com/pipalacademy/ipytail

# PipalHub - JupyterHub setup for [Pipal Academy][PA]

PipalHub is JuputerHub setup optimized for remote workshops of Pipal Academy.

It contains a JupyterHub server providing one Jupyter instance for each participant, a bunch of scripts to summarize changes and export notebooks as HTML so that instructor can quickly glance though the notebooks of the participants.

## Quick setup

There are some easy-install scripts that can be used to setup the node with all dependencies
that will be needed to run the server.

See the [section on adding users and packages](#adding-users-and-packages) after setup
for how to add users or pip dependencies.

### Easy install

#### `create-node.py` script (recommended)

This one script can be used from your local machine to create a new node on DigitalOcean and
get PipalHub up and running on it.

**Description:**

This script will create a DigitalOcean droplet with the given size and name, assign a DNS entry to it, and run the
setup-node.sh script on it with the given hostname + configured base domain.

Some of its default configuration can be found in the script after imports.
[These](https://github.com/pipalacademy/pipalhub/blob/b10a5fa8817c4f3e594a0bd4f5044c157f5092da/create-node.py#L14-L21)
can be changed if needed.

**Prerequisites:**

* `DIGITALOCEAN_TOKEN` to create a node and set DNS entry on it.
* One of your SSH keys should be saved on DigitalOcean. This is to run the setup script on a new node over SSH.
* DNS for `pipal.in` (configurable) domain must be served from DigitalOcean.

**Usage:**

```shell
$ git clone https://github.com/pipalacademy/pipalhub
$ cd pipalhub
$ DIGITALOCEAN_TOKEN="token_goes_here" python3 create-node.py --name alpha --size small --hostname alpha-lab.pipal.in
```

* `--name` can be a string: this will be the name of your droplet.
* `--size` can be one of small, medium, large. vCPUs / memory for each size are configured in the [`SIZES` dict](https://github.com/pipalacademy/pipalhub/blob/b10a5fa8817c4f3e594a0bd4f5044c157f5092da/create-node.py#L15-L19)
defined in create-node.py.
* `--hostname` is the subdomain that this domain will be assigned. For example, if `BASE_DOMAIN` is configured to be `pipal.in` in create-node.py, the node will
become accessible at `{hostname}.pipal.in`

#### `setup-node.sh` script

Once you have a node ready, this script can be used to install all the dependencies, setup SSL, and start serving JupyterHub.

Please note that `create-node.py` executes this script, so you don't have to do it separately.

**Description:**

`setup-node.sh` is a script to be run on the node that needs to be setup with all that is needed for the JupyterHub setup to work.
It assumes a fresh Ubuntu install, but it will work idempotently too. If some step fails due to some reason,
you can fix the cause and run this script again.

**Implementation details:**

It does these things:
- install nginx
- install docker
- clone this (pipalacademy/pipalhub) repository
- symlink path to this directory to `/var/www/pipalhub` (it's `tmp/` subdirectory will be used to serve from nginx)
- save the correct nginx configuration (corrected for hostname from sample one) to `etc/nginx/conf.d/lab.conf`
- symlink this to `/etc/nginx/conf.d`
- install certbot with nginx plugin
- use certbot to create SSL certificate (does not setup renewal)
- docker compose up
- reload nginx

**Prerequisites:**
* An Ubuntu 22.04 server with root access.
* Working directory should be `$HOME`

**Usage:**

```shell
$ setup-node.sh hostname.pipal.in
```

### Adding users and packages

> TODO: This functionality can be added to the dashboard service

To add users to JupyterHub server,

1. SSH into the machine
2. Open `$HOME/pipalhub/etc/jupyterhub/users.txt` in an editor (create one if it doesn't exist)
3. Add users one on each line, in the format `username:password`. See [`$HOME/pipalhub/etc/jupyterhub/users.txt.sample`](https://github.com/pipalacademy/pipalhub/blob/b10a5fa8817c4f3e594a0bd4f5044c157f5092da/etc/jupyterhub/users.txt.sample)
for an example of how this file should look.
4. Go to PipalHub directory (`$HOME/pipalhub/etc/jupyterhub/users.txt`).

```shell
dev@home:~$ ssh root@hostname.pipal.in  # 1. ssh into the host machine
$ cd pipalhub
$ vi etc/jupyterhub/users.txt # 2. open in editor
$ # 3. add users
$ docker compose restart # 4. for changes to take effect
```

### Implementation

#### Directory structure

This is the directory structure, after ignoring some directories / files that aren't relevant:

```
├── Readme.md
├── create-node.py
├── docker-compose.yml
├── etc
│   ├── jupyter
│   │   ├── jupyter_notebook_config.py
│   │   └── lab
│   │       └── docmanager.jupyterlab-settings
│   ├── jupyterhub
│   │   ├── jupyterhub_config.py
│   │   └── users.txt.sample
│   └── nginx
│       ├── conf.d
│       │   └── lab.conf.sample
│       └── default.conf
├── home
│   └── Readme.txt
├── services
│   └── dashboard_service
│       ├── dashboard_service.py
│       ├── javascripts
│       │   └── poll.js
│       ├── launch.sh
│       ├── requirements.txt
│       └── scripts
│           ├── build.py
│           ├── build.sh
│           └── ipytail.py
├── setup-node.sh
└── tmp
    └── Readme.txt
```

There is a single docker container that contains JupyterHub and student servers.
It is setup with docker compose. A web server configuration (nginx configuration provided)
should be setup on the host to expose this container over a domain.

The container also contains a [Dashboard service](#dashboard-service) that is a Flask app which
runs some action when a notebook is saved. For now, this is the [build script][ipytail] that
updates summaries of notebooks when a student makes a save. The `scripts/` directory stores these.
The `javascripts/` directory has a polling script that uses the endpoint exposed by dashboard-service
to allow a developer to perform some action on frontend when a particular event (such as save of a notebook)
is logged. For example, this can be used to notify the user on the frontend that an update is available
to the summary page.

Configuration files are kept in `etc/`. Of these `jupyterhub/` and `jupyter/` are for inside the
docker container and `nginx/` is for the host.

#### Container

The jupyterhub container is configured using `docker compose`. [`docker-compose.yml`](/docker-compose.yml) lists several volume mounts and an expose port.
The volume mounts are either for sharing configuration with the container or for ease of visibility for the trainer.

#### Dashboard service

Related issue: https://github.com/pipalacademy/pipalhub/issues/6

This is a JupyterHub-managed service, i.e. the related process is started and stopped by JupyterHub.
We only need to configure it in [`jupyterhub_config.py`](https://github.com/pipalacademy/pipalhub/blob/b10a5fa8817c4f3e594a0bd4f5044c157f5092da/etc/jupyterhub/jupyterhub_config.py#L565-L575),
with the command that needs to run.

Currently this is a Flask app that is started on port 10101 using environment variables
configured in `jupyterhub_config.py`. JupyterHub will also create a reverse proxy endpoint
on its server to this service. So, this dashboard service will be accessible at `https://hostname.pipal.in/services/dashboard`,
and we won't need some separate nginx configuration for this.

The `launch.sh` script for this installs dependencies needed for it to function with pip (flask, pydantic)
before starting it. This may change in the future, a possible solution would be to have a single
`requirements.txt` for the instance that comes with defaults but can be changed by the trainer.

##### /events endpoint

`/events` supports `GET` and `POST` methods.

`GET /events` can also be combined with filters as query params.

These are example requests/responses:

###### Create event:

```json
POST /events
{
    "type": "test-event",
    "user": "alice",
    "filename": "module1-day1.ipynb",
    "path": "/home/alice/module1-day1.ipynb",
    "timestamp": "2022-11-14T16:00:00.511Z"
}
--- response:
201 CREATED
{
    "id": 1,
    "type": "test-event",
    "user": "alice",
    "filename": "module1-day1.ipynb",
    "path": "/home/alice/module1-day1.ipynb",
    "timestamp": "2022-11-14T16:00:00.511000+00:00"
}
```

Note that if the client doesn't send a timestamp, the server won't raise an error but rather
default to using the current timestamp.

###### List events:

```json
GET /events
--- response:
200 OK
[
    {
        "id": 1,
        "type": "test-event",
        "user": "alice",
        "filename": "module1-day1.ipynb",
        "path": "/home/alice/module1-day1.ipynb",
        "timestamp": "2022-11-14T16:00:00.511000+00:00"
    },
    {
        "id": 2,
        "type": "test-event",
        "user": "bob",
        "filename": "module1-day1.ipynb",
        "path": "/home/bob/module1-day1.ipynb",
        "timestamp": "2022-11-15T16:00:00.511000+00:00"
    }
]
```

Listing can also have filters. Filtering can be done on any field in the returned JSON. Example:

```json
GET /events?user=alice
--- response:
[
    {
        "id": 1,
        "type": "test-event",
        "user": "alice",
        "filename": "module1-day1.ipynb",
        "path": "/home/alice/module1-day1.ipynb",
        "timestamp": "2022-11-14T16:00:00.511000+00:00"
    }
]
```

#### Configuration

There is a bunch of configuration in `etc/` that is needed for JupyterHub and JupyterLab to
function as we want.

##### `etc/jupyterhub/jupyterhub_config.py`

Important configurations set in this file:

* [`c.Spawner.default_url = '/lab'`](https://github.com/pipalacademy/pipalhub/blob/b10a5fa8817c4f3e594a0bd4f5044c157f5092da/etc/jupyterhub/jupyterhub_config.py#L822): This
sets the default page for a student server to the JupyterLab interface. (alternative is the
classic notebook, that can be achieved by setting this to `''` instead)
* [`c.Spawner.pre_spawn_hook = bootstrap_user_env`](https://github.com/pipalacademy/pipalhub/blob/b10a5fa8817c4f3e594a0bd4f5044c157f5092da/etc/jupyterhub/jupyterhub_config.py#L1005-L1015): Some
configuration can be set once and applied for all users, but sometimes this may not be possible
and we need to explicitly set configuration on a per-user basis. The pre-spawn-hook currently
does that before spawning the student server. It does that by copying some default configuration
to the per-user configuration directory.
* [`c.JupyterHub.services = ...`](https://github.com/pipalacademy/pipalhub/blob/b10a5fa8817c4f3e594a0bd4f5044c157f5092da/etc/jupyterhub/jupyterhub_config.py#L565-L575): This lists
[JupyterHub services](https://jupyterhub.readthedocs.io/en/stable/reference/services.html). We currently have one service called dashboard, as described [above](#dashboard-service).

##### `etc/jupyter/jupyter_notebook_config.py`

Note that this configuration may move to `jupyter_server_config.py` in the future, as is done
in later versions of Jupyter.

This configuration file is for the spawned Jupyter notebooks. It is shared by all users.

At the moment, this has an important responsibility to send a `"save-notebook"` event to
the [dashboard service](#dashboard-service) whenever someone saves a notebook. It does this
by setting a [`post_save_hook`](https://jupyter-notebook.readthedocs.io/en/stable/extending/savehooks.html),
a function that runs in the active user's environment when a save is made.

##### `etc/jupyter/lab/...`

This should house configuration that needs to be explicitly copied into per-user environments.
Currently there is only one such configuration for the docmanager plugin to default to a lower
autosave interval.

This is being done by the `pre_spawn_hook` in `etc/jupyterhub/jupyterhub_config.py`
at the moment, but should be moved elsewhere in the future. Ideally so that it can run whenever
a new system user is created rather than before spawn.

### Manual setup

Clone the repo:

```
$ git clone git://github.com/pipalacademy/pipalhub.git
$ cd pipalhub
```

Setup users:

```
$ cp etc/jupyterhub/users.txt.sample etc/jupyterhub/users.txt
```

Edit `etc/jupyterhub/users.txt` to add more users.


Setup nginx:

```
$ cd etc/nginx/conf.d
$ cp lab.conf.sample lab.conf
$ sudo ln -s "$(pwd)/lab.conf" /etc/nginx/conf.d/lab.conf
$ cd -
```

For production, cp lab-ssl.conf.sample to lab.conf and edit the file to set the hostname and ssl certificates.

Start the lab:

```
$ docker-compose up -d
```

Reload nginx:

```
$ sudo systemctl reload nginx
```
