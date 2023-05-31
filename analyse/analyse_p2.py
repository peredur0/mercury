#! /usr/bin/env python3
# coding: utf-8

"""
Analyse statistique sur les données de la phase 2.

"""

import matplotlib.pyplot as plt
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
    z_col = ['constante', 'coefficient', 'tx_erreur']
    h_col = ['nombre', 'ratio_unique', 'ratio_texte']

    query = f"""SELECT {', '.join([f'm.{col}' for col in m_col])}, 
            {', '.join([f'p.{col}' for col in p_col if col != 'cat'])},
            {', '.join([f'z.{col}' for col in z_col if col != 'cat'])},
            {', '.join([f'h.{col}' for col in h_col if col != 'cat'])},
            c.type 
            FROM stats_mots as m
            JOIN stat_ponct as p ON m.id_message=p.id_message
            JOIN messages as e ON m.id_message=e.id_message
            JOIN zipf as z ON m.id_message=z.id_message
            JOIN hapax as h ON m.id_message=h.id_message
            JOIN categories as c ON e.id_cat=c.id_cat
    """

    return pd.DataFrame(exec_query(cli, query), columns=m_col + p_col + z_col + h_col + ['type'])


def add_hist(ham, spam, feat, limit, bins, title, axe):
    axe.hist((ham[ham[feat] < limit][feat], spam[spam[feat] < limit][feat]),
             bins=bins, label=['ham', 'spam'])
    axe.legend(loc='upper right')
    axe.title.set_text(title)


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

    df_spam = g_stats[g_stats['type'] == 'spam']
    df_ham = g_stats[g_stats['type'] == 'ham']

    fig, ax = plt.subplots(nrows=3, ncols=2)
    fig.tight_layout(pad=0.5)
    add_hist(df_ham, df_spam, 'mots', 600, 30, "Répartition par nombre de mots", ax[0, 0])
    add_hist(df_ham, df_spam, 'mots_uniques', 500, 30, "Répartition par nombre de mots uniques",
             ax[0, 1])
    add_hist(df_ham, df_spam, 'mot_maj', 100, 30, "Répartition par nombre de mots en majuscules",
             ax[1, 0])
    add_hist(df_ham, df_spam, 'mot_cap', 100, 30, "Répartition par nombre de mots capitalisés",
             ax[1, 1])
    add_hist(df_ham, df_spam, 'char_min', 2000, 30, "Répartition par nombre de char en "
                                                    "minuscule", ax[2, 0])
    add_hist(df_ham, df_spam, 'char_maj', 200, 30, "Répartition par nombre de char en majuscule",
             ax[2, 1])
    plt.show()

    fig, ax = plt.subplots(nrows=2, ncols=2)
    fig.tight_layout(pad=0.5)
    add_hist(df_ham, df_spam, 'point', 30, 15, "Répartition par nombre de points", ax[0, 0])
    add_hist(df_ham, df_spam, 'virgule', 30, 15, "Répartition par nombre de virgules", ax[0, 1])
    add_hist(df_ham, df_spam, 'exclamation', 10, 10, "Répartition par nombre de points "
                                                     "d'exclamation", ax[1, 0])
    add_hist(df_ham, df_spam, 'interrogation', 60, 30, "Répartition par nombre de point "
                                                       "d'interrogation", ax[1, 1])
    plt.show()

    fig, ax = plt.subplots(nrows=2, ncols=2)
    fig.tight_layout(pad=0.5)
    add_hist(df_ham, df_spam, 'espace', 600, 30, "Répartition par nombre d'espaces", ax[0, 0])
    add_hist(df_ham, df_spam, 'tabulation', 30, 15, "Répartition par nombre de tab", ax[0, 1])
    add_hist(df_ham, df_spam, 'ligne', 300, 30, "Répartition par nombre de lignes", ax[1, 0])
    add_hist(df_ham, df_spam, 'ligne_vide', 50, 15, "Répartition par nombre de lignes vides",
             ax[1, 1])
    plt.show()

    # Distribution de zipf par message
    for e_type in ['ham', 'spam']:
        df = g_stats[g_stats['type'] == e_type]
        print('---', e_type.capitalize())
        print("Zipf:")
        print(df[['constante', 'coefficient', 'tx_erreur']].describe())
        print("Hapax:")
        print(df[['nombre', 'ratio_unique', 'ratio_texte']].describe())

    fig, ax = plt.subplots(nrows=2, ncols=3)
    fig.tight_layout(pad=0.5)
    add_hist(df_ham, df_spam, 'constante', 200, 30, "Répartition par constante calculée", ax[0, 0])
    add_hist(df_ham, df_spam, 'coefficient', 1.5, 30, "Répartition par coefficient", ax[0, 1])
    add_hist(df_ham, df_spam, 'tx_erreur', 1, 30, "Répartition par taux d'erreur ", ax[0, 2])
    add_hist(df_ham, df_spam, 'nombre', 200, 30, "Répartition par nombre d'hapax", ax[1, 0])
    add_hist(df_ham, df_spam, 'ratio_unique', 1, 30, "Répartition par ratio hapax/vocabulaire",
             ax[1, 1])
    add_hist(df_ham, df_spam, 'ratio_texte', 1, 30, "Répartition par ratio hapax/nombre de mots",
             ax[1, 2])
    plt.show()


