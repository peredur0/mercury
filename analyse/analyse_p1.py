#! /usr/bin/env python3
# coding: utf-8

"""
Analyses préliminaires de la phase 1.

    Graphiques :
        - Ratio HAM/SPAM
        - Ratio HAM/SPAM pour les liens (url, mail, telephone, nombres, prix)
        - Distribution HAM/SPAM pour les liens
"""

import matplotlib.pyplot as plt
import pandas as pd

from databases.psql_cmd import connect_db, exec_query
from databases.psql_db import secrets as psql_secrets


def get_p1_data():
    """
    Recupere les donnees de la phase 1
    - id_mail
    - categorie
    - liens
    :return: <pandas DF>
    """
    psql_cli = connect_db('mail_features_prod', psql_secrets.owner, psql_secrets.owner_pw,
                          psql_secrets.host, psql_secrets.port)

    column = ['id_message', 'type', 'url', 'mail', 'tel', 'nombre', 'prix']
    query = """select m.id_message, c.type, l.url, l.mail, l.tel, l.nombre, l.prix from messages 
    as m 
    join categories as c on m.id_cat = c.id_cat
    join liens as l on m.id_message = l.id_message"""

    df = pd.DataFrame(exec_query(psql_cli, query), columns=column)
    psql_cli.close()

    return df.set_index('id_message')


def set_bar_graph(data, feat, subplot, pos):
    """
    Affiche les statistiques générales d'une caracteristiques
    :param data: <DataFrame> Donnees mails
    :param feat: <str> caractéristique
    :param subplot: <Axes> axe pour l'affichage
    :param pos: position
    :return: <None>
    """
    df = data[data[feat] < 20].groupby(['type', data[feat]]).size()
    df.unstack(0).plot(kind='bar', ax=subplot[pos])


if __name__ == '__main__':
    df_all = get_p1_data()
    df_spam = df_all[df_all['type'] == 'spam']
    df_ham = df_all[df_all['type'] == 'ham']

    d_pie = df_all.groupby(['type']).size()
    fig, ax = plt.subplots()
    fig.suptitle('Répartition des ham/spam')
    ax.pie(d_pie, labels=d_pie.index, autopct='%1.1f%%')
    plt.show()

    print("Statistiques Liens")
    print("Gobales: \n", df_all.describe())
    print("Ham: \n", df_ham.describe())
    print("Spam: \n", df_spam.describe())

    fig, ax = plt.subplots(nrows=5, ncols=1)
    fig.suptitle("Distribution des mails en fonction du nombre de liens")
    fig.tight_layout(pad=0.5)
    position = 0
    for feat in ['url', 'mail', 'tel', 'nombre', 'prix']:
        set_bar_graph(df_all, feat, ax, position)
        position += 1
    plt.show()


