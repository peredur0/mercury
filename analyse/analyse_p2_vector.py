#! /usr/bin/env python3
# coding: utf-8

"""
Analyse de la vectorisation
"""

import pandas as pd
from databases import psql_cmd
from databases.psql_db import secrets as ps_secrets

if __name__ == '__main__':

    psql_db = "mail_features_prod"
    psql_cli = psql_cmd.connect_db(dbname=psql_db,
                                   user=ps_secrets.owner,
                                   passwd=ps_secrets.owner,
                                   host=ps_secrets.host,
                                   port=ps_secrets.port)

    query = "ALTER TABLE tfidf_vector ADD COLUMN IF NOT EXISTS somme DECIMAL"
    psql_cmd.exec_query(psql_cli, query)

    fields = [row['label'] for row in psql_cmd.get_data(psql_cli, 'tfidf_assoc', ['label'])]
    for row in psql_cmd.get_data(psql_cli, 'tfidf_vector', ['id_message']):
        id_message = row.get('id_message')
        query = (f"UPDATE tfidf_vector "
                 f"SET somme = (SELECT {'+'.join(fields)} FROM tfidf_vector "
                 f"WHERE id_message = {id_message}) "
                 f"WHERE id_message = {id_message}")
        psql_cmd.exec_query(psql_cli, query)

    query = (f"SELECT t.id_message, t.somme, c.type "
             f"FROM tfidf_vector as t "
             f"JOIN messages as m ON m.id_message = t.id_message "
             f"JOIN categories as c ON c.id_cat = m.id_cat "
             f"WHERE t.somme = 0")
    data = psql_cmd.exec_query(psql_cli, query)

    tmp_data = []
    if data:
        print(f"Nombre de mail avec une somme de vecteur nulle: {len(data)}")
        for row in data:
            row_data = {'id_message': row[0], 'vector_sum': row[1], 'type': row[2]}
            r_fields = ['point', 'virgule', 'exclamation', 'interrogation', 'espace',
                        'tabulation', 'ligne', 'ligne_vide']
            table = 'stat_ponct'
            result = psql_cmd.get_data(psql_cli, table, r_fields, f'id_message = {row[0]}')
            row_data.update(result[0])

            r_fields = ['mots_uniques', 'mots', 'char_min', 'char_maj', 'mot_cap']
            table = 'stats_mots'
            result = psql_cmd.get_data(psql_cli, table, r_fields, f'id_message = {row[0]}')
            row_data.update(result[0])

            r_fields = ['url', 'mail', 'tel', 'nombre', 'prix']
            table = 'liens'
            result = psql_cmd.get_data(psql_cli, table, r_fields, f'id_message = {row[0]}')
            row_data.update(result[0])

            r_fields = ['constante', 'coefficient', 'tx_erreur']
            table = 'zipf'
            result = psql_cmd.get_data(psql_cli, table, r_fields, f'id_message = {row[0]}')
            row_data.update(result[0])

            r_fields = ['ratio_unique', 'ratio_texte', 'nombre']
            table = 'hapax'
            result = psql_cmd.get_data(psql_cli, table, r_fields, f'id_message = {row[0]}')
            row_data.update(result[0])

            tmp_data.append(row_data)
            print(row_data)

            query = (f"SELECT id_message, mot, freq_corpus, freq_doc_all, freq_doc_spam, "
                     f"freq_doc_ham "
                     f"FROM mots_document "
                     f"JOIN mot_corpus ON mots_document.id_mot = mot_corpus.id_mot "
                     f"WHERE id_message = {row[0]}")
            q_data = psql_cmd.exec_query(psql_cli, query)
            for entry in q_data:
                print(entry)
    psql_cli.close()
