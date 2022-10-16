#! /usr/bin/env python3
# coding: utf-8

"""
Module d'insertion de données dans la base postgreSQL
"""

# import
import sys
import psycopg2
import json


def create_db(nom, owner, user, passwd, host, port):
    """ Creer une nouvelle base de donnees.
    :param nom: <str> nom de la base
    :param owner: <str> proprietaire de la base
    :param user: <str> utilisateur
    :param passwd: <str> mot de passe
    :param host: <str> adresse du serveur
    :param port: <str> port de connection
    :return: None
    """
    client_psql = psycopg2.connect(user=user, password=passwd, host=host, port=port)
    client_psql.autocommit = True
    cursor = client_psql.cursor()

    cursor.execute("DROP DATABASE IF EXISTS {};".format(nom))
    cursor.execute("CREATE DATABASE {};".format(nom))
    cursor.execute("ALTER DATABASE {} OWNER TO {};".format(nom, owner))
    client_psql.close()


def connect_db(database, user, passwd, host, port):
    """ Connexion a la base de donnees Postgres.
    Penser a fermer la connexion
    :param database: <str> nom de la base de donnees
    :param user: <str> utilisateur autoriser a push les donnees
    :param passwd: <str> mot de passe
    :param host: <str> localisation reseau de la bdd
    :param port: <str> port de connexion
    :return: <psycopg2.extension.connection> objet connexion à la bdd
    """
    try:
        client_psql = psycopg2.connect(database=database, user=user, password=passwd, host=host, port=port)
    except psycopg2.Error as e:
        print("Erreur de connexion : \n{}".format(e), file=sys.stderr)
        return None

    client_psql.autocommit = True
    return client_psql


def create_table(client_psql, nom, champs):
    """
    Creer une nouvelle table dans la base de donnees
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param nom: <str> nom de la table
    :param champs: <dict> nom : [type, options]
    :return:
    """
    curseur = client_psql.cursor()
    curseur.execute("DROP TABLE IF EXISTS {}".format(nom))

    expression = "CREATE TABLE {}".format(nom)
    expression += "("
    for key in champs:
        expression += " {} {},".format(str(key), " ".join(champs[key]))
    expression = expression[:-1]    # Suppression de la virgule finale
    expression += ")"

    curseur.execute(expression)


def create_index(client_psql, nom, table, colonne):
    """ Index sur les hash des messages
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param nom: <str> nom de l'index
    :param table: <str> table sur laquelle creer l'index
    :param colonne: <str> colonne cible
    :return:
    """
    query = "CREATE UNIQUE INDEX {} ON {}({})".format(nom, table, colonne)
    exec_query(client_psql, query)


def insert_data(client_psql, table, data):
    """
    Insere les donnees d'un dictionnaire dans une table de la base de donnees PSQL
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param table: <str> La table dans a remplir
    :param data: <dict> {colonne: valeur}
    :return: None
    """
    cols = ','.join([str(c) for c in data.keys()])
    vals = ','.join([str(v) if (type(v) != str) else f"'{v}'" for v in data.values()])
    query = f"INSERT INTO {table}({cols}) VALUES ({vals})"

    exec_query(client_psql, query)


def insert_subst(client_psql, data):
    """ Insere les donnees de substitutions dans la table
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param data: <dict> donnees a inserer
    :return:
    """
    val = "{}, {}, {}, {}, {}, {}".format(
        data['id_message'],
        data['data']['URL'],
        data['data']['MAIL'],
        data['data']['TEL'],
        data['data']['NOMBRE'],
        data['data']['PRIX']
    )

    query = '''INSERT INTO substitutions(id_message, url, mail, telephone, nombres, prix)
                VALUES ({})'''.format(val)

    exec_query(client_psql, query)


def insert_mots(client_psql, data):
    """ Insertion des mots
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param data: <dict> donnees a inserer
    :return:
    """
    query = 'SELECT mot FROM mots'
    result_q = [m[0] for m in exec_query(client_psql, query)]

    for mot in data["mots"].keys():
        # Table mots
        if mot in result_q:
            query = "SELECT occurences FROM mots WHERE mot LIKE '{}'".format(mot)
            result_o = int(exec_query(client_psql, query)[0][0])
            query = "UPDATE mots SET occurences = {} WHERE mot LIKE '{}'".format(
                result_o + data["mots"][mot],
                mot)
            exec_query(client_psql, query)

        else:
            query = "INSERT INTO mots (mot, taille, occurences) VALUES ('{}', {}, {})".format(
                mot,
                len(mot),
                data["mots"][mot]
            )
            exec_query(client_psql, query)

        # Table occurences mail mot
        query = "SELECT id_mot FROM mots WHERE mot LIKE '{}'".format(mot)
        result_id = int(exec_query(client_psql, query)[0][0])

        query = "INSERT INTO occurences_mail(id_message, id_mot, occurences) VALUES ({}, {}, {})".format(
            data['id_message'],
            result_id,
            data["mots"][mot]
        )
        exec_query(client_psql, query)


def exec_query(client_psql, query):
    """ Execute une query dans la base PSQL
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param query: <str> query a appliquer
    :return: <list> vide ou sortie du select
    """
    cursor = client_psql.cursor()

    try:
        cursor.execute(query)
        if query.upper().find("SELECT", 0, 6) >= 0:
            return cursor.fetchall()
        return []
    except psycopg2.Error as e:
        print("Erreur d'execution de la requete : {}".format(e), file=sys.stderr)
        print("requete : {}".format(query))
        return []


def messageid_from_hash(client_psql, mes_hash):
    """ Recupere l'id du message depuis le hash
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param mes_hash:
    :return: <int> identifiant du message ou -1
    """
    query = "SELECT id_message FROM messages WHERE hash like '{}'".format(mes_hash)
    result = exec_query(client_psql, query)
    return -1 if not result else result[0][0]


if __name__ == '__main__':

    conf = json.load(open("db_mapping.json", 'r'))
    db = list(conf.keys())[0]
    create_db(nom=db, owner="data", user="postgres", passwd="postgres", host="localhost", port="5432")

    conn = connect_db(database=db, user="data", passwd="data", host="localhost", port='5432')
    for t in conf[db].keys():
        create_table(conn, t, conf[db][t])

    conn.close()
    exit(0)
