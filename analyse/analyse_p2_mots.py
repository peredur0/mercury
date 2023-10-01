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

from databases import psql_cmd
from databases.psql_db import secrets as ps_secrets

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

    # Préparation de la nouvelle table
    tf_idf = {psql_db: {"tfidf": {}}}


    psql_cli.close()
