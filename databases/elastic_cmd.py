#! /usr/bin/env python3
# coding: utf-8

"""
Fonctions utilisées pour la relation avec la base elasticsearch
"""

import sys
from elasticsearch import Elasticsearch
from elasticsearch import exceptions, AuthenticationException, AuthorizationException

# metadata
__author__ = "Martial GOEHRY"
__licence__ = "GNU GPL v3"
__version__ = "0.0.0"
__status___ = "development"


def es_connect(server, creds, crt):
    """
    Connexion au serveur ElasticSearch
    :param server: <str> - adresse:port du serveur
    :param creds: <list> - identifiants de connexion
    :param crt: <str> - chemin vers le certificat CA
    :return: <es_client> - connexion ES
    """
    client = Elasticsearch(server, api_key=creds, ca_certs=crt)

    try:
        client.search()
        client.indices.get(index="*")
        return client

    except (exceptions.ConnectionError, AuthenticationException, AuthorizationException) as err:
        print("ES:conn - Informations client ElasticSearch :\n\t", err)
        client.close()
        return None


def es_create_indice(es_cli, index, mapping):
    """
    Créer un indice s'il n'existe pas déjà
    :param es_cli: Client ElasticSearch
    :param index: <str> - nom de l'indice
    :param mapping: <dict> - mapping de l'indice
    :return: None ou <str> le nom de l'indice
    """
    indices = es_cli.indices.get(index='*')
    if indices and index in indices:
        print("Warning: Indice {} déjà présent".format(index))

    res = es_cli.indices.create(index=index, mappings=mapping)

    if not res['acknowledged']:
        print("Error : Echec de la création de l'indice {}".format(index))


def es_index_doc(es_cli, index, doc, ls_id):
    """ Index un document dans la base ES
    :param es_cli: Client ElasticSearch
    :param index: <str> index ou stocker les donnees
    :param doc: <dict> donnees du document
    :param ls_id: <list> liste des id de l'index
    :return: <None>
    """
    id_doc = doc['hash']
    if id_doc in ls_id:
        print("Warning: {} deja present".format(id_doc), file=sys.stderr)
        return

    resp = es_cli.index(index=index, document=doc)
    print("ES:index - ID = {} - STATUS = {}".format(id_doc, resp['result']))
    es_cli.indices.refresh(index=index)
    ls_id.append(doc['hash'])


# todo : Vérifier une fois les données importées - ICI
def es_get_all(es_cli, index, query):
    """
    Récupère
    :param es_cli:
    :param index:
    :param query:
    :return:
    """
    data = []

    # Récupération du nom

    return data


if __name__ == '__main__':
    import json
    from databases import secrets

    email_mapping = json.load(open('mail_mapping.json', 'r'))
    cli = es_connect(secrets.serveur, (secrets.apiid, secrets.apikey), secrets.ca_cert)
    index = "test_mail1"

    print(cli)

    outp = cli.indices.create(index=index, mappings=email_mapping)
    print(cli.indices.get(index='*').keys())
    print(outp['acknowledged'])
    print(cli.indices.delete(index=index))

    cli.close()

    exit(0)
