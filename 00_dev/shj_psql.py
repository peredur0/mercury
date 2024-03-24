#! /usr/bin/env python3
# coding:utf-8

"""
Script principal du projet SpamHamJam
"""

# import
import json
import sys
import nltk
import hashlib

import shj_import as shji
import bak_shj_lem as shjl
import shj_clear as shjc
import shj_pgs_func as shjp


# metadata
__author__ = "Martial GOEHRY"
__licence__ = "GNU GPL v3"
__version__ = "0.0.0"
__status___ = "development"
__email__ = "martial.goehry@gmail.com"

# globales
categories = {'spam': 0, 'ham': 1, 'csv': 2}


def run_db(conf, owner, owner_pass, admin, admin_pass, host, port):
    """ Creation de la base de donnees a partir d'un fichier de configuration
    Si la table existe elle sera supprimee
    :param conf: <str> fichier json de configuration
    :param owner: <str> proprietaire de la base (data)
    :param owner_pass: <str> mot de passe du proprietaire (data)
    :param admin: <str> utilisateur pour creer la base (postgres)
    :param admin_pass: <str> mot de passe pour creer la base (postgres)
    :param host: <str> adresse du serveur
    :param port: <int> port de connection
    :return: <str> nom de la base
    """
    config = json.load(open(conf, 'r'))
    db = list(config.keys())[0]
    shjp.create_db(db, owner, admin, admin_pass, host, str(port))
    conn = shjp.connect_db(db, owner, owner_pass, host, str(port))

    for table in config[db].keys():
        shjp.create_table(conn, table, config[db][table])

    shjp.create_index(conn, "hash_index", "messages", "hash")

    conn.close()
    return db


def insert_message_psql(conn, chemin, message, categorie):
    """ Insere un message dans la base
    :param conn: <psycopg2.extension.connection> connexion a la base psql
    :param chemin: <str> chemin vers le fichier
    :param message: <email.message.EmailMessage> message non traité
    :param categorie: <str> ham, spam ou csv
    :return:
    """
    subst = {}
    lem = {}

    body = shji.extract_body(message)
    corp = shjc.clear_texte(body)

    # Mise en forme
    corp = shjl.extrait_subst(corp, subst)
    nb_mots = shjl.extrait_lem(corp, lem)

    # Meta data
    empreinte = hashlib.md5(body.encode()).hexdigest()
    sujet, exp = shji.extract_meta(message)
    cat = categories[categorie]

    # Table messages
    data_message = {
        'hash': empreinte,
        'path': chemin,
        'expediteur': exp,
        'categorie': cat,
        'mots_uniques': len(lem),
        'nombre_mots': nb_mots
    }

    if data_message['nombre_mots'] == 0:
        print("ERR : {} - Pas de donnees textuelles".format(chemin), file=sys.stderr)
        return

    message_id = shjp.messageid_from_hash(conn, empreinte)
    if message_id >= 0:
        print("ERR : {} - Message deja present".format(chemin), file=sys.stderr)
        return

    shjp.insert_message(conn, data_message)
    print("{} - inserer".format(empreinte), end=" ")

    # Table substitutions
    message_id = shjp.messageid_from_hash(conn, empreinte)
    data_substitution = {
        'id_message': message_id,
        "data": subst
    }

    shjp.insert_subst(conn, data_substitution)
    print("- substitution", end=" ")

    # Tables mots et occurences_mail
    data_mots = {
        'id_message': message_id,
        "mots": lem
    }

    shjp.insert_mots(conn, data_mots)
    print("- mots")


def run_dossier_psql(conn, repertoire, categorie):
    """
    Lance l'importation a partir d'un dossier.
    Tous les mails du dossier doivent être de la même categorie
    :param conn: <psycopg2.extension.connection> connexion a la base psql
    :param repertoire: <str> chemin d'acces au dossier
    :param categorie: <str> ham, spam ou csv
    :return:
    """
    for file in shji.list_files(repertoire):
        chemin = file
        message = shji.import_from_file(file)
        insert_message_psql(conn, chemin, message, categorie)


def run_csv_psql(conn, chemin, categorie):
    """
    Lance l'importation a partir d'un fichier csv.
    Tous les mails du fichier doivent être de la même categorie
    champs du csv : fichier, message
    :param conn: <psycopg2.extension.connection> connexion a la base psql
    :param chemin: <str> chemin d'acces au fichier
    :param categorie: <str> ham, spam ou csv
    :return:
    """
    print("Recuperation des information csv : {}".format(chemin))
    data = shji.import_from_csv(chemin)[1:]

    for mail in data:
        chemin = mail[0]
        message = mail[1]
        insert_message_psql(conn, chemin, message, categorie)


def main_psql():
    nltk.download('wordnet')
    nltk.download('punkt')

    # Creation de la base de donnees.
    print(80 * '-')
    print("Creation DB")
    print(80 * '-')
    db = run_db("tables.json", "data", "data", "postgres", "postgres", "localhost", 5432)
    conn = shjp.connect_db(db, "data", "data", "localhost", 5432)

    # Table categories
    shjp.insert_cat(conn, categories)

    # Importation des fichiers
    spams = ['./data/spam', './data/spam_2']
    ham = ['./data/easy_ham', './data/easy_ham_2', './data/hard_ham']
    csvfile = ['./data/csv/emails.csv']

    for rep in spams:
        print(80 * '-')
        print("IMPORT : {}".format(rep))
        print(80 * '-')
        run_dossier_psql(conn, rep, 'spam')

    for rep in ham:
        print(80 * '-')
        print("IMPORT : {}".format(rep))
        print(80 * '-')
        run_dossier_psql(conn, rep, 'ham')

    for file in csvfile:
        print(80 * '-')
        print("IMPORT : {}".format(file))
        print(80 * '-')
        run_csv_psql(conn, file, 'csv')

    print('FINI')
    conn.close()


if __name__ == '__main__':
    main_psql()
    exit(0)

