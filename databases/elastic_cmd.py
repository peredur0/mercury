#! /usr/bin/env python3
# coding: utf-8

"""
Fonctions utilisées pour la relation avec la base elasticsearch
"""

import sys

import elasticsearch
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
    :return: None
    """
    indices = es_cli.indices.get(index='*')
    if indices and index in indices:
        print("Warning: Indice {} déjà présent".format(index))
        return

    res = es_cli.indices.create(index=index, mappings=mapping)

    if not res['acknowledged']:
        print("Error : Echec de la création de l'indice {}".format(index))


def es_index_doc(es_cli, index, doc):
    """ Index un document dans la base ES
    :param es_cli: Client ElasticSearch
    :param index: <str> index ou stocker les donnees
    :param doc: <dict> donnees du document
    :return: <None>
    """
    id_doc = doc['hash']

    if es_document_exists(es_cli, index, id_doc):
        return

    es_cli.index(index=index, document=doc)
    es_cli.indices.refresh(index=index)


def es_document_exists(es_cli, index, hash):
    """
    Regader dans l'index si le hash du document est déjà présent
    :param es_cli: client elastic
    :param index: <str> Index à chercher dedans
    :param hash: <str> hash du document
    :return: <bool> True si le hash du document est déjà présent False sinon
    """
    try:
        resp = es_cli.search(index=index, query={"match": {"hash": hash}})
    except elasticsearch.NotFoundError as err:
        print("Error : hash", err, file=sys.stderr)
        return None

    return True if resp['hits']['total']['value'] == 1 else False


def es_get_doc_nb(es_cli, index, query):
    """
    Retourne le nombre de documents qui matchent la query dans un index elasticsearch
    :param es_cli: client elastic
    :param index: <str> index de recherche
    :param query: <dict> corp de la requête
    :return: <int> nombre de documents qui matchent la requête
    """

    return es_cli.count(index=index, query=query)['count']


def es_get_all(es_cli, index, query):
    """
    Récupère tous les documents d'un index selon la query
    :param es_cli: client elastic
    :param index: <str> index de recherche
    :param query: <dict> requete à utilisé
    :return:
    """
    documents = []

    return documents


if __name__ == '__main__':
    from databases.elastic_docker import secrets

    cli = es_connect(secrets.serveur, (secrets.apiid, secrets.apikey), 'ca.crt')
    if not cli:
        exit(1)

    index = "test_import_all0"
    query_all = {"match_all": {}}
    query_spam = {"match": {"categorie": "spam"}}
    print(es_get_doc_nb(cli, index, query_all))
    print(es_get_doc_nb(cli, index, query={"match": {"categorie": "spam"}}))
    print(es_get_doc_nb(cli, index, query={"match": {"categorie": "ham"}}))

    # --- get_all_document dev
    SORT = "hash"
    SIZE = 100
    count = 0
    nb_all = es_get_doc_nb(cli, index, query_all)
    nb_spam = es_get_doc_nb(cli, index, query_spam)

    p1 = cli.search(index=index, size=SIZE, sort={SORT: "asc"}, query=query_spam)
    signet = p1['hits']['hits'][-1]['sort']
    for hit in p1['hits']['hits']:
        count += 1

    p2 = cli.search(index=index, size=SIZE, sort={SORT: "asc"}, query=query_spam, search_after=signet)
    signet = p2['hits']['hits'][-1]['sort']
    for hit in p2['hits']['hits']:
        count += 1

    while count < nb_all:
        pn = cli.search(index=index, size=SIZE, sort={SORT: "asc"}, query=query_spam, search_after=signet)
        try:
            signet = pn['hits']['hits'][-1]['sort']
        except IndexError:
            print("WARNING", pn, signet)
            break

        for hit in pn['hits']['hits']:
            count += 1

    print("FINAL", count)

    # ---

    cli.close()

    exit(0)
