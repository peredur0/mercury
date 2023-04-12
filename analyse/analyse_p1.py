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

    return df


def ratio_simple():
    """
    Ratio simple HAM/SPAM
    :return: None
    """


if __name__ == '__main__':
    df = get_p1_data()
