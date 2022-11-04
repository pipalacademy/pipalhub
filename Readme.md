# PipalHub - JupyterHub setup for [Pipal Academy][PA]

PipalHub is JuputerHub setup optimized for remote workshops of Pipal Academy.

It contains a JupyterHub server providing one Jupyter instance for each participant, a bunch of scripts to summarize changes and export notebooks as HTML so that instructor can quickly glance though the notebooks of the participants.

## Implementation

It is implemented using docker-compose with the following docker containers, and nginx.

* jupyterhub - for running jupyterhub server
* build - script to [summarize the notebooks][ipytail] and export them as HTML
* nginx - exposing the jupyterhub to the external world and handling SSL

[PA]: https://pipal.in/
[ipytail]: https://github.com/pipalacademy/ipytail

## How to Setup

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
