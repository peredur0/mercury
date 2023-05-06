#! /usr/bin/env python3
# coding: utf-8

"""
Fonctions utilisée pour le stockage des informations statistiques.
Stockage dans une base SQLlite
"""

import sqlite3
import json
import sys

import tqdm


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


def sl_select(client, requete):
    """
    Récupère les données des champs
    :param client: <sqlite.connection> client sqlite
    :param requete: <str> table à interrogée
    :return: <dict>
    """
    cursor = client.execute(requete)
    rows = cursor.fetchall()

    return rows


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


####################################################################################################
#           Statistiques Récolte                                                                   #
####################################################################################################
def print_stats(categorie, etape, cli):
    """
    affiche les statistiques pour une étape
    :param categorie: <str> catégorie
    :param etape: <str> l'étape d'intérêt
    :param cli: <sqlite.connection> client vers la base sqlite
    :return: <None>
    """
    print('\t{}, '.format(categorie.upper()), end=' ')
    cursor = cli.execute("SELECT mails, mots, mots_uniques "
                         "FROM {} "
                         "WHERE etape LIKE '{}';".format(categorie, etape))
    ligne1 = cursor.fetchone()
    if not ligne1 or len(ligne1) != 3:
        print("Error :", ligne1)
        return

    print('mails: {} \tmots: {}\t mots uniques: {}'.format(ligne1[0], ligne1[1], ligne1[2]))


def stats_recolte(categorie, stats_dict, liste):
    """
    Fonction de récupération des données stastiques pour mercury
    :param categorie: <str> ham, spam
    :param stats_dict: <dict> au format de "stats_temp"
    :param liste: <list> des chemins à analyser
    :return: <list> liste des mots uniques pour fusion avec les autres catégories
    """
    m_uniq = []
    for file in tqdm.tqdm(liste,
                          desc="-- Stats - étape : Récolte {}...".format(categorie),
                          leave=False,
                          file=sys.stdout,
                          ascii=True):
        try:
            mots = open(file, 'r').read().split()
            stats_dict['mots'] += len(mots)
            for mot in mots:
                if mot not in m_uniq:
                    m_uniq.append(mot)
        except UnicodeDecodeError:
            continue

    stats_dict['etape'] = "recolte"
    stats_dict['mots_uniques'] = len(m_uniq)
    stats_dict['mails'] = len(liste)

    print("-- Stats - étape : Récolte {}... OK".format(categorie))
    return m_uniq


def stats_creation_doc(categorie, stats_dict, liste):
    """
    Récupération des infos statistiques après create_document
    :param categorie: <str> catégorie de mail
    :param stats_dict: <dict> selon template de "stats_temp"
    :param liste: <list> liste des documents nettoyés
    :return: <list> liste des mots uniques pour fusion avec les autres catégories
    """
    m_uniq = []
    for doc in tqdm.tqdm(liste,
                         desc="-- Stats - étape : Nettoyage {}...".format(categorie),
                         leave=False,
                         file=sys.stdout,
                         ascii=True):
        stats_dict["mots"] += len(doc["message"].split())

        for mot in doc["message"].split():
            if mot not in m_uniq:
                m_uniq.append(mot)

    stats_dict["mots_uniques"] = len(m_uniq)
    stats_dict["mails"] = len(liste)
    stats_dict["etape"] = "creation document"

    print("-- Stats - étape : création documents {}... OK".format(categorie))
    return m_uniq


def stats_mise_en_base(categorie, stats_dict, liste):
    """
    Récupération des statistiques après la mise en base.
    ! Car les mails déjà présent en base sont rejetés.
    :param categorie: <str> categorie de mail
    :param stats_dict: <dict> selon template de "stats_temp"
    :param liste: <list> liste des documents extraits de la base ES
    :return: <list> liste des mots uniques pour fusion avec les autres catégories
    """
    m_uniq = []
    for doc in tqdm.tqdm(liste,
                         desc="-- Stats - étape : Mise en base {}...".format(categorie),
                         leave=False,
                         file=sys.stdout,
                         ascii=True):
        message = doc["_source"]["message"].split()
        stats_dict["mots"] += len(message)
        for mot in message:
            if mot not in m_uniq:
                m_uniq.append(mot)

    stats_dict["mots_uniques"] = len(m_uniq)
    stats_dict["mails"] = len(liste)
    stats_dict["etape"] = "mise en base"

    print("-- Stats - étape : Mise en base {}... OK".format(categorie))
    return m_uniq


def stats_process(chemin, etape, data):
    """
    Gère le processus de récolte et d'affichage des statistiques pour chaque étape
    :param chemin: <str> chemin vers le fichier base de données
    :param etape: <str> intitulé de l'étape
    :param data: <dict> données à traiter {'ham': <list>, 'spam': <list>}
    :return: <None>
    """
    fonctions = {'recolte': stats_recolte,
                 'creation document': stats_creation_doc,
                 'mise en base': stats_mise_en_base}

    func = fonctions.get(etape.lower(), None)
    if not func:
        print("Erreur : étape {} inconnue, dispo - {}".format(etape, fonctions.keys()), sys.stderr)
        return

    # Données pour SQLite
    stats_temp = {
        'etape': 'template',
        'mails': 0,
        'mots': 0,
        'mots_uniques': 0
    }
    stats_spam = stats_temp.copy()
    stats_ham = stats_temp.copy()
    stats_globales = stats_temp.copy()

    uniq_spam = func('spam', stats_spam, data.get('spam', []))
    uniq_ham = func('ham', stats_ham, data.get('ham', []))

    stats_globales['mails'] = stats_spam.get('mails', 0) + stats_ham.get('mails', 0)
    stats_globales['mots'] = stats_spam.get('mots', 0) + stats_ham.get('mots', 0)
    stats_globales['mots_uniques'] = len(set(uniq_ham + uniq_spam))
    stats_globales['etape'] = etape

    # - Mise en base des statistiques
    sl_client = sl_connect(chemin)

    print("--- Sauvegarde des stats de l'étape: {}...".format(etape), end=' ')
    sl_insert(sl_client, 'globales', stats_globales)
    sl_insert(sl_client, 'ham', stats_ham)
    sl_insert(sl_client, 'spam', stats_spam)
    print('OK')

    print("Données stats de l'étape: {}:".format(etape))
    for elem in ['ham', 'spam', 'globales']:
        print_stats(elem, etape, sl_client)

    sl_client.close()
    return


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
