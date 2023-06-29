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


def connect_db(user, passwd, host, port, dbname=""):
    """ Connexion a la base de donnees Postgres.
    Penser a fermer la connexion
    :param user: <str> utilisateur autoriser a push les donnees
    :param passwd: <str> mot de passe
    :param host: <str> localisation reseau de la bdd
    :param port: <str> port de connexion
    :param dbname: <str> nom de la base de donnees
    :return: <psycopg2.extension.connection> objet connexion à la bdd
    """
    try:
        client_psql = psycopg2.connect(dbname=dbname, user=user, password=passwd, host=host, port=port)
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
    fields = []
    cursor = client_psql.cursor()

    for key, value in champs.items():
        if key in ['pk', 'fk']:
            continue
        fields.append(f"{key} {' '.join(value)}")

    if 'pk' in champs.keys():
        fields.append(f"PRIMARY KEY ({','.join(champs.pop('pk'))})")

    if 'fk' in champs.keys():
        for name, val in champs['fk'].items():
            constr = f"CONSTRAINT {name} FOREIGN KEY({val.pop(0)}) REFERENCES {val.pop(0)}"
            if val:
                constr += f" ON DELETE {val.pop(0)}"
            fields.append(constr)

    query = f"CREATE TABLE {nom} ({', '.join(fields)})"

    try:
        cursor.execute(query)
    except psycopg2.Error as f_err:
        print(f_err, file=sys.stderr)
    else:
        print(f"Table '{nom}' created")


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
    Les clés du dictionnaire doivent correspondre aux colonnes de la table.
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee
    :param table: <str> La table dans a remplir
    :param data: <dict> {colonne: valeur}
    :return: None
    """
    cols = ','.join([str(c) for c in data.keys()])
    vals = ','.join([str(v) if (type(v) != str) else f"'{v}'" for v in data.values()])
    query = f"INSERT INTO {table}({cols}) VALUES ({vals})"

    exec_query(client_psql, query)


def get_data(client_psql, table, champs, clause=None):
    """
    Récupère les données de la base.
    :param client_psql: <psycopg2.extension.connection> object connexion vers une base de donnee.
    :param table: <str> table a scroller.
    :param champs: <list> champs à récupérer.
    :param clause: <str> Clause WHERE
    :return: <dict>
    """
    query = f"SELECT {','.join(champs)} FROM {table}"
    if clause:
        query += f" WHERE {clause}"

    result = exec_query(client_psql, query)
    return [dict(zip(champs, ligne)) for ligne in result]


def insert_document_init(client_psql, data, id_cat):
    """
    Insert un nouveau document dans la base PSQL.
    Tables impactées : messages, liens
    :param client_psql:
    :param data:
    :param id_cat:
    :return:
    """
    insert_data(client_psql, 'messages', {'hash': data['hash'], 'id_cat': id_cat})
    id_message = get_data(client_psql, 'messages', ['id_message'], f"hash LIKE '{data['hash']}'")[0]['id_message']

    liens = data['liens']
    liens.update({'id_message': id_message})
    insert_data(client_psql, 'liens', liens)


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
        print("requete : {}".format(query), file=sys.stderr)
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


def create_user(admin, adm_pass, user, password, host, port):
    """
    Création d'un nouvel utilisateur PSQL
    :return: None
    """
    cli_psql = psycopg2.connect(user=admin, password=adm_pass, host=host, port=port)
    cli_psql.autocommit = True

    query = f"SELECT 1 FROM pg_roles WHERE rolname='{user}'"
    result = exec_query(cli_psql, query)

    if not result:
        query = f"CREATE ROLE {user} LOGIN PASSWORD '{password}'"
        exec_query(cli_psql, query)
        print(f"User '{user}' créé")
        return
    print(f"User '{user}' déjà existant")


if __name__ == '__main__':
    from hashlib import md5
    conf = json.load(open("./psql_db/db_mapping.json", 'r'))
    db = list(conf.keys())[0]

    create_db(nom=db, owner="data", user="postgres", passwd="postgres", host="localhost", port="5433")
    conn = connect_db(database=db, user="data", passwd="data", host="localhost", port='5433')
    for t in conf[db].keys():
        create_table(conn, t, conf[db][t])

    insert_data(conn, "categories", {'type': 'spam'})
    print(get_data(conn, "categories", ['id_cat'], "type LIKE 'spam'"))
    insert_data(conn, "messages", {'hash': md5('iju'.encode()).hexdigest(), 'id_cat': 1})
    insert_data(conn, "messages", {'hash': md5('aza'.encode()).hexdigest(), 'id_cat': 1})
    out = get_data(conn, "messages", ['id_message', 'hash', 'id_cat'])
    print(out)
    insert_data(conn, 'liens', {'id_message': 1, "mail": 3})
    print(get_data(conn, "liens", ['id_message', 'url', 'mail', 'telephone']))
    conn.close()
    exit(0)
