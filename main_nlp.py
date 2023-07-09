#! /usr/bin/env python3
# coding: utf-8

"""
Module de traitement du texte

"""
import json
import re
import sys

import nltk
import stanza
import torch.cuda
from nltk.corpus import stopwords
from databases import elastic_cmd, psql_cmd
from databases.elastic import secrets as es_secrets
from databases.psql_db import secrets as ps_secrets
from traitement import stats


def recup_mails(es_index):
    """
    Récuperation des mails dans la base psql
    :param es_index: <str> nom de l'index ES où recupérer les données
    :return: <dict> Dictionnaire avec les données des mails
    """
    es_cli = elastic_cmd.es_connect(es_secrets.serveur, (es_secrets.apiid, es_secrets.apikey),
                                    es_secrets.ca_cert)

    print("-- Récupération des messages...", end=' ')
    data = {entry.get('_source').get('hash'): entry.get('_source').get('message')
            for entry in elastic_cmd.es_get_all(es_cli, es_index, sort={'hash': 'asc'},
                                                query={'match_all': {}})}
    print('OK')
    es_cli.close()
    return data


def lemmatise(message, stopwds, pipeline, pattern):
    """
    Réduit un texte avec les principes de lemmatisation.
    Retire les ponctuations et les stopwords
    :param message: <str> message à traiter
    :param stopwds: <list> liste des stopwords
    :param pipeline: <stanza.Pipeline> Pipeline nlp
    :param pattern: <re.compile> r'<\w+>'
    :return: <list> message lemmatisé sous forme de liste de mot
    """
    doc = pipeline(message)
    lemma = [mot.lemma for phrase in doc.sentences for mot in phrase.words]
    return [lem.lower() for lem in lemma if re.match(pattern, lem) and lem.lower() not in stopwds]


if __name__ == '__main__':
    nltk.download("stopwords")
    en_stopwd = set(stopwords.words('english'))
    pipe = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma')
    print("=== Phase 2 : Traitement du langage ===")

    psql_conf = json.load(open("./databases/psql_db/db_mapping_prod_nlp_add.json"))
    psql_db = list(psql_conf.keys())[0]
    psql_cli = psql_cmd.connect_db(dbname=psql_db,
                                   user=ps_secrets.owner,
                                   passwd=ps_secrets.owner,
                                   host=ps_secrets.host,
                                   port=ps_secrets.port)

    print("Ajout des nouvelles tables pour la vectorisation...")
    for table in psql_conf[psql_db].keys():
        psql_cmd.create_table(psql_cli, table, psql_conf[psql_db][table])

    p_data = recup_mails('import_prod')

    pat = re.compile(r'\w+')
    for key, value in p_data.items():
        try:
            freq_data = stats.frequence_mot(lemmatise(value, en_stopwd, pipe, pat))
        except TypeError:
            print(f"Type Error : {key}")
        except torch.cuda.OutOfMemoryError:
            print(f"Memory error : {key}")
        else:
            # Ajouter les données dans la table
            pass
        finally:
            # Ajouter données dans la table nlp status
            pass
    print("END")

    psql_cli.close()
