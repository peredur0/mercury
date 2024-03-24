#! /usr/bin/env python3
# coding:utf-8

"""
Partie ElasticSearch pour SpanHamJam
"""

# import
import hashlib
import sys

from elasticsearch import Elasticsearch, exceptions

import shj_clear
import shj_import
import bak_shj_lem


# metadata
__author__ = "Martial Goehry"
__licence__ = "GNU GPL v3"
__version__ = "0.0.0"
__status__ = "development"
__email__ = "martial.goehry@gmail.com"


# Globales
server = "https://localhost:9200"
creds = ["elastic", "elastic123"]
liste_index = []
MAX_RESULTS = 10000000


def gen_document(chemin, message, categorie):
    """ creation d'un document pour l'importation dans ElasticSearch
    :param chemin: <str> chemin d'acces au fichier
    :param message: <email.message.EmailMessage> message non traité
    :param categorie: <str> ham, spam ou inconnu
    :return:
    """
    subst = {}

    brut = shj_import.extract_body(message)
    corp = shj_clear.clear_texte(brut)
    corp = bak_shj_lem.extrait_subst(corp, subst)

    sujet, expediteur = shj_import.extract_meta(message)

    doc = {
        'hash': hashlib.md5(brut.encode()).hexdigest(),
        'chemin': chemin,
        'categorie': categorie,
        'sujet': sujet,
        'expediteur': expediteur,
        'nombres_mots': len(corp.split()),
        'substitutions': subst,
        'message': corp,
    }

    return doc


def get_ids(es_cli, index):
    """ Recupere les indices deja present dans l'index
    :param es_cli: client elasticsearch
    :param index: <str> index des données
    :return: <list> liste des index
    """
    resp = es_cli.search(index=index, query={"match_all": {}}, size=MAX_RESULTS)
    ids = [h['_id'] for h in resp['hits']['hits']]
    return ids


def post_message_es(es_cli, index, doc, ls_id):
    """ Post un document dans la base ES
    :param es_cli: Client ElasticSearch
    :param index: <str> index ou stocker les donnees
    :param doc: <dict> donnees du document
    :param ls_id: <list> liste des id de l'index
    :return:
    """
    id_doc = doc['hash']
    if id_doc in ls_id:
        print("Warning: {} deja present".format(id_doc), file=sys.stderr)
        return

    resp = es_cli.index(index=index, document=doc)
    print("ID = {} - STATUS = {}".format(id_doc, resp['result']))
    es_cli.indices.refresh(index=index)
    ls_id.append(doc['hash'])


def run_dossier_es(es_cli, rep, cat, index):
    """ Importation de fichiers dans un dossier
    :param es_cli: Client Elastic
    :param rep: repertoire
    :param cat: categorie (ham, spam, inconnu)
    :param index: index ou stocker
    :return: None
    """
    for file in shj_import.list_files(rep):
        message = shj_import.import_from_file(file)
        post_message_es(es_cli, index, gen_document(file, message, cat), liste_index)


def run_csv_es(es_cli, fichier, cat, index):
    """
    :param es_cli: Client Elastic
    :param fichier: <str> fichier CSV
    :param cat: categorie
    :param index: index ou stocker
    :return:
    """
    print("Recuperation des information csv : {}".format(fichier))
    data = shj_import.import_from_csv(fichier)[1:]

    for mail in data:
        chemin = mail[0]
        message = mail[1]
        post_message_es(es_cli, index, gen_document(chemin, message, cat), liste_index)


if __name__ == '__main__':

    es_client = Elasticsearch(server, http_auth=creds, ca_certs="./data/ca.crt")
    index_mail = 'mails_2'

    try:
        es_info = es_client.info()
        print("ElasticSearch information client :", es_info)
    except exceptions.ConnectionError as err:
        print("\nElasticSearch client info ERREUR:", err)
        exit(1)

    spams = ['./data/spam', './data/spam_2']
    ham = ['./data/easy_ham', './data/easy_ham_2', './data/hard_ham']
    # csvfile = ['./data/inconnu/emails.csv']
    csvfile = []

    for rep in spams:
        print(80 * '-')
        print("IMPORT : {}".format(rep))
        print(80 * '-')
        run_dossier_es(es_client, rep, 'spam', index_mail)

    for rep in ham:
        print(80 * '-')
        print("IMPORT : {}".format(rep))
        print(80 * '-')
        run_dossier_es(es_client, rep, 'ham', index_mail)

    for file in csvfile:
        print(80 * '-')
        print("IMPORT : {}".format(file))
        print(80 * '-')
        run_csv_es(es_client, file, 'inconnu', index_mail)

    exit(0)
