#! /usr/bin/env python3
# coding: utf-8

"""
Phase d'analyse des mots utilisés dans les corpus
    X mots les plus présents dans le corpus
    X mots les plus présents dans chaque catégorie
    X mots moins présents dans une catégorie, mais très présent dans l'autre
    X mots au moins deux fois plus présent dans une catégorie que dans l'autre
    X mots avec un ratio d'apparition fort dans une catégorie par rapport à l'autre
"""
import sys
import math
import tqdm
from databases import psql_cmd
from databases.psql_db import secrets as ps_secrets


def tfidf_vectorise(client_psql, id_message, nb_documents):
    """
    Vectorise un message avec la technique TF-IDF.
    Nécessite de récupérer les éléments en base.
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param id_message: <int> Identifiant du message dans la base
    :param nb_documents: <int> nombre total de documents dans le corpus
    :return: <dict> données à insérer
    """
    vector = {'id_message': id_message}
    associations = psql_cmd.get_data(client_psql, 'tfidf_assoc', ['id_mot', 'label'])

    for entry in associations:
        id_mot = entry.get('id_mot')
        col_label = entry.get('label')

        res = psql_cmd.get_data(client_psql, 'mots_document', ['occurrence'],
                                f' id_message = {id_message} AND id_mot = {id_mot}')
        term_freq = res[0].get('occurrence', 0) if res else 0

        res = psql_cmd.get_data(client_psql, 'mot_corpus', ['freq_doc_all'],
                                f' id_mot = {id_mot}')
        doc_freq = res[0].get('freq_doc_all', None) if res else None

        cell_value = term_freq * math.log(nb_documents/doc_freq) if doc_freq else 0
        vector[col_label] = cell_value

    return vector


if __name__ == '__main__':
    unwanted = ['spamassassinsightings',
                'deathtospamdeathtospamdeathtospam',
                'spamassassindevel']
    
    limit = 200
    queries = [
        f"SELECT mot FROM mot_corpus ORDER by freq_corpus DESC LIMIT {limit};",
        f"SELECT mot FROM mot_corpus ORDER by freq_doc_spam DESC LIMIT {limit};",
        f"SELECT mot FROM mot_corpus ORDER by freq_doc_ham DESC LIMIT {limit};",
        f"SELECT mot FROM mot_corpus ORDER by freq_doc_ham, freq_doc_spam DESC LIMIT {limit};",
        f"SELECT mot FROM mot_corpus ORDER by freq_doc_spam, freq_doc_ham DESC LIMIT {limit};",
        f"SELECT mot FROM mot_corpus WHERE freq_doc_ham >= 2*freq_doc_spam ORDER BY freq_doc_ham "
        f"DESC LIMIT {limit};",
        f"SELECT mot FROM mot_corpus WHERE freq_doc_spam >= 2*freq_doc_ham ORDER BY freq_doc_spam "
        f"DESC LIMIT {limit};",
        f'SELECT mot, freq_doc_ham/freq_doc_spam as "ratio ham/spam" FROM mot_corpus WHERE '
        f'freq_doc_ham > 0 AND freq_doc_spam > 0 ORDER BY "ratio ham/spam" DESC LIMIT {limit};'
        f'SELECT mot, freq_doc_spam/freq_doc_ham as "ratio spam/ham" FROM mot_corpus WHERE '
        f'freq_doc_ham > 0 AND freq_doc_spam > 0 ORDER BY "ratio spam/ham" DESC LIMIT {limit};'
    ]

    psql_db = "mail_features_prod"
    psql_cli = psql_cmd.connect_db(dbname=psql_db,
                                   user=ps_secrets.owner,
                                   passwd=ps_secrets.owner,
                                   host=ps_secrets.host,
                                   port=ps_secrets.port)
    
    mots = []
    for query in queries:
        result = psql_cmd.exec_query(psql_cli, query)
        for row in result:
            mot = row[0]
            if mot not in mots and mot not in unwanted and len(mot) > 2:
                mots.append(mot)

    # Préparation de la base
    tfidf_assoc_field = {"id_mot": ['INT', 'UNIQUE', 'NOT NULL'],
                         "label": ['VARCHAR'],
                         "fk": {"fk_mot": ['id_mot', 'mot_corpus(id_mot)', 'CASCADE']}}
    psql_cmd.create_table(psql_cli, 'tfidf_assoc', tfidf_assoc_field)

    tfidf_vector_fields = {"id_message": ['INT', 'UNIQUE', 'NOT NULL'],
                           "fk": {'fk_message': ['id_message', 'messages(id_message)', 'CASCADE']}}
    n_label = 0
    for mot in mots:
        result = psql_cmd.get_data(psql_cli, 'mot_corpus', ['id_mot'], f"mot LIKE '{mot}'")
        if not result:
            print(f"id_mot non récupéré pour {mot}", file=sys.stderr)
            continue

        label = f"feat_mot_{n_label}"
        data = {'id_mot': result[0]['id_mot'], 'label': label}
        psql_cmd.insert_data(psql_cli, 'tfidf_assoc', data)

        tfidf_vector_fields[label] = ['DECIMAL']
        n_label += 1

    psql_cmd.create_table(psql_cli, 'tfidf_vector', tfidf_vector_fields)

    # Vectorisation des messages
    result = psql_cmd.exec_query(psql_cli, "SELECT COUNT(id_message) FROM nlp_status WHERE "
                                           "success = true")
    n_docs = result[0][0]

    result = psql_cmd.get_data(psql_cli, 'nlp_status', ['id_message'], 'success = true')
    for row in tqdm.tqdm(result, desc='-- Vectorisation', leave=False, file=sys.stdout, ascii=True):
        id_mess = row.get('id_message')
        vecteur = tfidf_vectorise(psql_cli, id_mess, n_docs)
        psql_cmd.insert_data(psql_cli, 'tfidf_vector', vecteur)

    psql_cli.close()
