#! /usr/bin/env python3
# coding: utf-8

"""
Fonctions utilisée pour le stockage des informations statistiques.
Stockage dans une base SQLlite
"""

import sqlite3
import json


def sl_connect(path):
    """
    Connection avec un base sqlite
    :param path: <str> chemin d'accès au fichier
    :return: <sqlite.connection> client sqlite
    """
    return sqlite3.connect(path)


def sl_create_tables(client, schema_file):
    """
    Créer les tables dans la base
    :param client: <sqlite.connection> client sqlite vers la base
    :param schema_file: <str> fichier de configuration des tables
    :return: None
    """
    schema = json.load(open(schema_file, 'r'))

    for table, champs in schema.items():
        params = ', '.join(["{} {}".format(k, ' '.join(v)) for k, v in champs.items()])
        client.execute("DROP TABLE IF EXISTS {};".format(table))
        client.execute("CREATE TABLE {} ({});".format(table, params))
        print("SQLITE table {} : CREATED".format(table))


def sl_select(client, table, champs):
    """
    Récupère les données des champs
    :param client: <sqlite.connection> client sqlite
    :param table: <str> table à interrogée
    :param champs: <list> liste des champs à selectionné
    :return: <dict>
    """

    return None


def sl_insert(client, table, data):
    """
    Insère des données données dans une table
    :param client: <sqlite.connection> client sqlite
    :param table: <str> table à remplir
    :param data: <dict> dictionnaire avec les valeurs {champs: valeur}
    :return: None
    """
    # Récupération du type des champs défini dans la base
    schema = {}
    for ligne in client.execute("PRAGMA table_info({});".format(table)):
        schema[ligne[1]] = ligne[2]

    # préparation de la requête
    noms = []
    valeurs = []
    for nom, valeur in data.items():
        if nom not in schema.keys():
            print("Warning - SQLITE champs '{}' non présent dans la table '{}'".format(nom, table))
            continue

        if not valeur:
            continue

        noms.append(nom)

        if schema[nom].upper() == 'TEXT':
            valeurs.append("'{}'".format(valeur))
        else:
            valeurs.append(str(valeur))

    # Mise en base
    client.execute("INSERT INTO {} ({}) VALUES ({});".format(table, ', '.join(noms), ', '.join(valeurs)))
    client.commit()


if __name__ == '__main__':
    conf = 'sqlite_db/table_stats_conf.json'

    client = sl_connect("./sqlite_db/test_table.db")
    sl_create_tables(client, conf)

    data = {"etape": 'traitement1',
            "mails": 5,
            'mot': 3
            }

    sl_insert(client, 'globales', data)
    print(client.execute("SELECT * FROM globales;").fetchone())

    client.close()

    exit(0)
