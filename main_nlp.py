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
import tqdm
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


def insert_mot(client_psql, id_mes, word, occurrence):
    """
    Insère les mots dans la base et les update si besoin
    :param client_psql: <psycopg2.connection> client postgres
    :param id_mes: <int> id du message dans la base
    :param word: <str> mot à charger
    :param occurrence: <int> fréquence du mot dans le document
    :return: None
    """
    m_query = f"SELECT EXISTS(SELECT id_mot FROM mot_corpus WHERE mot LIKE '{word}')"
    if (False,) in psql_cmd.exec_query(client_psql, m_query):
        psql_cmd.insert_data(client_psql, 'mot_corpus', {'mot': word,
                                                         'freq_corpus': 0,
                                                         'freq_doc_all': 0,
                                                         'freq_doc_spam': 0,
                                                         'freq_doc_ham': 0})

    try:
        id_mot = psql_cmd.get_data(client_psql, 'mot_corpus', ['id_mot'],
                                   f"mot LIKE '{word}'")[0].get('id_mot')
    except IndexError:
        print(f"Index error avec '{mot}'")
        return

    t_query = (f"SELECT c.type "
               f"FROM messages as m "
               f"JOIN categories as c "
               f"ON m.id_cat = c.id_cat AND m.id_message = {id_mes}")
    cat = psql_cmd.exec_query(client_psql, t_query)[0][0]

    mc_data = psql_cmd.get_data(client_psql, 'mot_corpus', ['freq_corpus', f'freq_doc_{cat}',
                                                            'freq_doc_all'],
                                f"id_mot = {id_mot}")[0]

    m_query = f"UPDATE mot_corpus SET " \
              f"freq_corpus = {mc_data.get('freq_corpus', 0) + occurrence}, " \
              f"freq_doc_{cat} = {mc_data.get(f'freq_doc_{cat}', 0) + 1}, " \
              f"freq_doc_all = {mc_data.get(f'freq_doc_all', 0) + 1} " \
              f"WHERE id_mot = {id_mot}"
    psql_cmd.exec_query(client_psql, m_query)

    psql_cmd.insert_data(client_psql, 'mots_document', {'id_message': id_mes,
                                                        'id_mot': id_mot,
                                                        'occurrence': occurrence})


if __name__ == '__main__':
    nltk.download("stopwords")
    en_stopwd = set(stopwords.words('english'))
    pipe = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma')
    print("=== Phase 2 : Traitement du langage ===")

    """
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
    """
    p_data = recup_mails('import_prod')
    pat = re.compile(r'\w+')
    """    
    for key, value in tqdm.tqdm(p_data.items(),
                                desc='-- NLP process',
                                leave=False,
                                file=sys.stdout,
                                ascii=True):
        id_message = psql_cmd.get_data(psql_cli, "messages", ['id_message'],
                                       f"hash LIKE '{key}'")[0].get('id_message')
        if not id_message:
            print(f"Message ID not found: hash '{key}'")
            continue

        query = f"SELECT EXISTS(SELECT id_message FROM nlp_status WHERE id_message = {id_message})"
        if (True, ) in psql_cmd.exec_query(psql_cli, query):
            print(f"Message {id_message} - {key} already processed")
            continue

        status_data = {'id_message': id_message, 'success': True}
        try:
            freq_data = stats.frequence_mot(lemmatise(value, en_stopwd, pipe, pat))
        except TypeError:
            status_data['success'] = False
            status_data['raison'] = "Type error"
        except torch.cuda.OutOfMemoryError:
            status_data['success'] = False
            status_data['raison'] = "Memory error"
        else:
            for mot, freq in freq_data.items():
                insert_mot(psql_cli, id_message, mot, freq)
        finally:
            psql_cmd.insert_data(psql_cli, "nlp_status", status_data)
    print("END")

    psql_cli.close()
    """
