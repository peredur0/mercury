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
    conn = psycopg2.connect(user=user, password=passwd, host=host, port=port)
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("DROP DATABASE IF EXISTS {};".format(nom))
    cursor.execute("CREATE DATABASE {};".format(nom))
    cursor.execute("ALTER DATABASE {} OWNER TO {};".format(nom, owner))
    conn.close()


def connect_db(db, user, passwd, host, port):
    """ Connexion a la base de donnees Postgres.
    Penser a fermer la connexion
    :param db: <str> nom de la base de donnees
    :param user: <str> utilisateur autoriser a push les donnees
    :param passwd: <str> mot de passe
    :param host: <str> localisation reseau de la bdd
    :param port: <str> port de connexion
    :return: <psycopg2.extension.connection> objet connexion à la bdd
    """
    try:
        conn = psycopg2.connect(database=db, user=user, password=passwd, host=host, port=port)
    except psycopg2.Error as e:
        print("Erreur de connexion : \n{}".format(e), file=sys.stderr)
        return None

    conn.autocommit = True
    return conn


def create_table(conn, nom, champs):
    """
    Creer une nouvelle table dans la base de donnees
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param nom: <str> nom de la table
    :param champs: <dict> nom : [type, options]
    :return:
    """
    curseur = conn.cursor()
    curseur.execute("DROP TABLE IF EXISTS {}".format(nom))

    expression = "CREATE TABLE {}".format(nom)
    expression += "("
    for key in champs:
        expression += " {} {},".format(str(key), " ".join(champs[key]))
    expression = expression[:-1]    # Suppression de la virgule finale
    expression += ")"

    curseur.execute(expression)


def create_index(conn, nom, table, colonne):
    """ Index sur les hash des messages
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param nom: <str> nom de l'index
    :param table: <str> table sur laquelle creer l'index
    :param colonne: <str> colonne cible
    :return:
    """
    query = "CREATE UNIQUE INDEX {} ON {}({})".format(nom, table, colonne)
    exec_query(conn, query)


def insert_message(conn, data):
    """ Insere donnees dans la table messages
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param data: <dict> donnees a inserer
    :return:
    """
    val = "'{}', '{}', '{}', {}, {}, {}".format(
        data['hash'],
        data['path'],
        data['expediteur'],
        data['categorie'],
        data['mots_uniques'],
        data['nombre_mots']
    )

    query = '''INSERT INTO messages(hash, path, expediteur, categorie, mots_uniques, nombre_mots)
                VALUES ({})'''.format(val)

    exec_query(conn, query)


def insert_subst(conn, data):
    """ Insere les donnees de substitutions dans la table
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
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

    exec_query(conn, query)


def insert_mots(conn, data):
    """ Insertion des mots
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param data: <dict> donnees a inserer
    :return:
    """
    query = 'SELECT mot FROM mots'
    result_q = [m[0] for m in exec_query(conn, query)]

    for mot in data["mots"].keys():
        # Table mots
        if mot in result_q:
            query = "SELECT occurences FROM mots WHERE mot LIKE '{}'".format(mot)
            result_o = int(exec_query(conn, query)[0][0])
            query = "UPDATE mots SET occurences = {} WHERE mot LIKE '{}'".format(
                result_o + data["mots"][mot],
                mot)
            exec_query(conn, query)

        else:
            query = "INSERT INTO mots (mot, taille, occurences) VALUES ('{}', {}, {})".format(
                mot,
                len(mot),
                data["mots"][mot]
            )
            exec_query(conn, query)

        # Table occurences mail mot
        query = "SELECT id_mot FROM mots WHERE mot LIKE '{}'".format(mot)
        result_id = int(exec_query(conn, query)[0][0])

        query = "INSERT INTO occurences_mail(id_message, id_mot, occurences) VALUES ({}, {}, {})".format(
            data['id_message'],
            result_id,
            data["mots"][mot]
        )
        exec_query(conn, query)


def insert_cat(conn, data):
    """
    ajouter les categories de mail:
        spam - 0
        ham - 1
        csv - 2
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param data: <dict> donnees de categories de mail
    :return:
    """
    for key, value in data.items():
        query = "INSERT INTO categories(id_cat, type) VALUES ({}, '{}')".format(
            value,
            key
        )
        exec_query(conn, query)


def exec_query(conn, query):
    """ Execute une query dans la base PSQL
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param query: <str> query a appliquer
    :return: <list> vide ou sortie du select
    """
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        if query.upper().find("SELECT", 0, 6) >= 0:
            return cursor.fetchall()
        return []
    except psycopg2.Error as e:
        print("Erreur d'execution de la requete : {}".format(e), file=sys.stderr)
        print("requete : {}".format(query))
        return []


def messageid_from_hash(conn, hash):
    """ Recupere l'id du message depuis le hash
    :param conn: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param hash:
    :return: <int> identifiant du message ou -1
    """
    query = "SELECT id_message FROM messages WHERE hash like '{}'".format(hash)
    result = exec_query(conn, query)
    return -1 if not result else result[0][0]


if __name__ == '__main__':

    conf = json.load(open("tables.json", 'r'))
    db = list(conf.keys())[0]
    create_db(nom=db, owner="data", user="postgres", passwd="postgres", host="localhost", port="5432")

    conn = connect_db(db=db, user="data", passwd="data", host="localhost", port='5432')
    for t in conf[db].keys():
        create_table(conn, t, conf[db][t])

    conn.close()
    exit(0)
