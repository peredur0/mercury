#! /usr/bin/env python3
# coding: utf-8

"""
Module d'outil pour docker
"""
import sys

import docker
import docker.errors


def container_up(name):
    """
    Verifie l'état du conteneur.
    :param name: <str> nom du container
    :return: <bool>
    """
    # docker_socket = "unix://var/run/docker.sock"
    # docker_cli = docker.DockerClient(docker_socket)
    docker_cli = docker.DockerClient()

    try:
        conteneur = docker_cli.containers.get(name)
    except docker.errors.NotFound as e:
        # print(f"Vérifier nom du conteneur '{name}' - {e.explanation}", file=sys.stderr)
        return False
    else:
        conteneur_state = conteneur.attrs['State']
        return conteneur_state['Status'] == "running"


if __name__ == '__main__':
    print(container_up('docker-es01-1'))
    print(container_up('docker_es01'))
    exit(0)
