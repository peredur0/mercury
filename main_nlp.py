#! /usr/bin/env python3
# coding: utf-8

"""
Module de traitement du texte

"""
import re
import nltk
import stanza
from nltk.corpus import stopwords
from databases import elastic_cmd, psql_cmd
from databases.elastic import secrets as es_secrets
from databases.psql_db import secrets as ps_secrets


def recup_mails(es_index):
    """
    Récuperation des mails dans la base psql
    :param es_index: <str> nom de l'index ES où recupérer les données
    :return: <dict> Dictionnaire avec les données des mails
    """
    es_cli = elastic_cmd.es_connect(es_secrets.serveur, (es_secrets.apiid, es_secrets.apikey),
                                    es_secrets.ca_cert)
    data = {}
    for cat in ['spam', 'ham']:
        print("-- Récupération des {}...".format(cat), end=' ')
        data[cat] = {entry.get('_source').get('hash'): entry.get('_source').get('message')
                     for entry in elastic_cmd.es_get_all(es_cli, es_index, sort={'hash': 'asc'},
                                                         query={'match': {'categorie': cat}})}
        print('OK')
    return data


def lemmatise(message, stopwds, pipeline):
    """
    Réduit un texte avec les principes de lemmatisation.
    Retire les ponctuations et les stopwords
    :param message: <str> message à traiter
    :param stopwds: <list> liste des stopwords
    :param pipeline: <stanza.Pipeline> Pipeline nlp
    :return: <list> message lemmatisé sous forme de liste de mot
    """
    doc = pipeline(message)
    lemma = [mot.lemma for phrase in doc.sentences for mot in phrase.words]
    return [lem for lem in lemma if re.match(r'\w+', lem) and lem not in stopwds]


if __name__ == '__main__':
    nltk.download("stopwords")
    en_stopwd = set(stopwords.words('english'))
    pipe = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma')
    print("=== Phase 2 : Traitement du langage ===")

    p_data = recup_mails('import_prod')
    psql_cli = psql_cmd.connect_db('mail_features_prod', ps_secrets.owner, ps_secrets.owner,
                                   ps_secrets.host, ps_secrets.port)

    # Création des nouvelles tables des mots

    # Récupération de tous les mots message par message.


    # Exemple
    messag = pipe("Barack Obama was born in Hawaii the January. I'm living in France."
                  "\nYou are near me")
    liste_2 = lemmatise(messag, en_stopwd, pipe)

