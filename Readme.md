# PipalHub - JupyterHub setup for [Pipal Academy][PA]

PipalHub is JuputerHub setup optimized for remote workshops of Pipal Academy. 

It contains a JupyterHub server providing one Jupyter instance for each participant, a bunch of scripts to summarize changes and export notebooks as HTML so that instructor can quickly glance though the notebooks of the participants.

## Implementation

It is implemented using docker-compose with the following docker containers.

* jupyterhub - for running jupyterhub server
* build - script to [summarize the notebooks][ipytail] and export them as HTML
* nginx - exposing the jupyterhub to the external world and handling SSL

[PA]: https://pipal.in/
[ipytail]: https://github.com/pipalacademy/ipytail
