#! /usr/bin/env python3
# coding: utf-8

"""
Analyse statistique sur les données de la phase 2.

"""

import matplotlib as plt
import pandas as pd

from databases.psql_cmd import connect_db, exec_query
from databases.psql_db import secrets as psql_secrets


def get_p2_mots(cli):
    """
    Recuperation des données de la table mot de la phase 2
    :param cli: <PSQL client>
    :return: <pandas DF>
    """

    column = ['mots_uniques', 'mots', 'char_min', 'char_maj', 'mot_maj', 'mot_cap', 'cat']
    query = f"""SELECT {', '.join([f'm.{col}' for col in column if col != 'cat'])}, c.type 
    FROM stats_mots as m
    JOIN messages as e ON m.id_message=e.id_message
    JOIN categories as c ON e.id_cat=c.id_cat
    """
    df = pd.DataFrame(exec_query(cli, query), columns=column)
    return df


def get_p2_ponct(cli):
    """
    Recuperation des données de la table ponct de la phase2
    :param cli: <PSQL Client>
    :return: <pandas DF>
    """
    column = ['point', 'virgule', 'exclamation', 'interrogation', 'tabulation', 'espace',
              'ligne', 'ligne_vide', 'cat']
    query = f"""SELECT {', '.join([f'p.{col}' for col in column if col != 'cat'])}, c.type 
    FROM stat_ponct as p
    JOIN messages as e ON p.id_message=e.id_message
    JOIN categories as c ON e.id_cat=c.id_cat
    """
    df = pd.DataFrame(exec_query(cli, query), columns=column)
    return df


def get_p2_data(cli):
    """
    Recupere toutes les données statistiques de l'étape 2
    :param cli: <PSQL Client>
    :return: <pandas DF>
    """
    m_col = ['mots_uniques', 'mots', 'char_min', 'char_maj', 'mot_maj', 'mot_cap']
    p_col = ['point', 'virgule', 'exclamation', 'interrogation', 'tabulation', 'espace',
             'ligne', 'ligne_vide']

    query = f"""SELECT {', '.join([f'm.{col}' for col in m_col])}, 
            {', '.join([f'p.{col}' for col in p_col if col != 'cat'])}, 
            c.type 
            FROM stats_mots as m
            JOIN stat_ponct as p ON m.id_message=p.id_message
            JOIN messages as e ON m.id_message=e.id_message
            JOIN categories as c ON e.id_cat=c.id_cat
    """

    return pd.DataFrame(exec_query(cli, query), columns=m_col + p_col + ['type'])


if __name__ == '__main__':
    cli = connect_db('mail_features_prod', psql_secrets.owner, psql_secrets.owner_pw,
                     psql_secrets.host, psql_secrets.port)

    display_lim = pd.get_option('display.max_columns')
    pd.set_option('display.max_columns', None)

    print('-- Recherche statistique')
    g_stats = get_p2_data(cli)

    print('--- Globales')
    print("Mots:")
    print(g_stats[['mots', 'mots_uniques', 'mot_cap', 'mot_maj']].describe())
    print("Char:")
    print(g_stats[['char_min', 'char_maj']].describe())
    print("Ponctuation:")
    print(g_stats[['point', 'virgule', 'exclamation', 'interrogation']].describe())
    print("Espace + Lignes:")
    print(g_stats[['tabulation', 'espace', 'ligne', 'ligne_vide']].describe())

    for e_type in ['ham', 'spam']:
        df = g_stats[g_stats['type'] == e_type]
        print('---', e_type.capitalize())
        print("Mots:")
        print(df[['mots', 'mots_uniques', 'mot_cap', 'mot_maj']].describe())
        print("Char:")
        print(df[['char_min', 'char_maj']].describe())
        print("Ponctuation:")
        print(df[['point', 'virgule', 'exclamation', 'interrogation']].describe())
        print("Espace + Lignes:")
        print(df[['tabulation', 'espace', 'ligne', 'ligne_vide']].describe())

    cli.close()

