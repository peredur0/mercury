#! /usr/bin/env python3
# coding: utf-8

"""
Phase 1: collecte et mise en base
    1. Importation des fichiers mail (récolte)
    2. Récupération du corps, préparation pour la mise en base (create_document)
    3. Stockage des informations importantes dans la base ElasticSearch (mise en base)

    A chaque étape on calcule par catégorie (Spam et Ham) et globalement:
        - le nombre de document
        - le nombre de mots
        - le nombre de mots unqiues
"""

import os
import platform
import sys
import warnings
import hashlib
# import magic
import langdetect
import json
import tqdm
from importation import mail_load
from traitement import nettoyage
from tool import docker_cmd
from databases import elastic_cmd, sqlite_cmd, psql_cmd
from databases.elastic import secrets as es_secrets
from databases.psql_db import secrets as psql_secrets


warnings.filterwarnings('ignore')


####################################################################################################
#           Importation des fichiers                                                               #
####################################################################################################
def importation(chemin):
    """
    Importation du fichier mail ou CSV
    :param chemin: <str> chemin d'accès au mail
    :return: [(<str>, <email.message.emailMessage>)] : chemin, mail
    """
    if not os.path.exists(chemin):
        return None

    # if magic.from_file(chemin, mime=True) == 'application/csv':
    #    return mail_load.import_from_csv(chemin)

    mail = mail_load.import_from_file(chemin)
    if mail:
        return mail
    return None


####################################################################################################
#           Création du document                                                                   #
####################################################################################################
def create_document(mail, categorie):
    """
    Extraction du message
    récupération des métadonnées
    traitement sommaire du message
    gestion de la catégorie de mail
    ajout de données chiffrées
    filtrage de la langue
    :param mail: <email.message.EmailMessage>
    :param categorie: <str> categorie de mail: ham, spam, ou inconnu
    :return: <dict>
    """
    corp = mail_load.extract_body(mail)
    corp, liens = nettoyage.clear_texte_init(corp)
    sujet, expediteur = mail_load.extract_meta(mail)

    if not corp:
        return None

    try:
        lang = langdetect.detect(corp)
    except langdetect.lang_detect_exception.LangDetectException:
        return None

    if lang != 'en':
        return None

    if categorie.lower() not in ['spam', 'ham']:
        categorie = 'inconnu'

    doc = {
        'hash': hashlib.md5(corp.encode()).hexdigest(),
        'categorie': categorie.lower(),
        'sujet': sujet,
        'expediteur': expediteur,
        'message': corp,
        'langue': lang,
        'liens': liens
    }
    return doc


def create_doc_process(categorie, liste):
    """
    Porcessus de création de document avec une barre de progression nested
    :param categorie: <str> Catégorie de mail, Ham ou Spam
    :param liste: <list>
    :return:
    """
    docs = []
    for fichier in tqdm.tqdm(liste,
                             desc="-- Importation {} ...".format(categorie.upper()),
                             leave=False,
                             ascii=True,
                             file=sys.stdout):

        message = importation(fichier)
        if message:
            m_doc = create_document(message, categorie)
            if m_doc:
                docs.append(m_doc)

    print("-- Importation - Création {}... OK".format(categorie))
    return docs


####################################################################################################
#          Phase 1: collecte et mise en base                                                       #
####################################################################################################
if __name__ == '__main__':
    # Globales
    DEV = False

    sqlite_db = './databases/sqlite_db/stats_dev.db' if DEV else \
        './databases/sqlite_db/stats_prod.db'

    # Vérification des accès docker
    print("=== Vérification des conteneurs Docker ===")
    for cont in ['docker-es01-1', 'docker-kibana-1', 'docker_pgadmin_1', 'docker_pgdb_1']:
        if not docker_cmd.container_up(cont):
            print(f"* Conteneur '{cont}' non présent")
            ques = input("Continuer [O] [N] ? ")
            if ques.upper() == 'O':
                continue
            else:
                print("Arret")
                exit(1)
        print(f"* Conteneur '{cont}'... OK")

    # Début
    print("=== Phase 1 : collecte & mise en base ===")
    print("== Création de la base SQLITE")
    sl_cli = sqlite_cmd.sl_connect(sqlite_db)
    sqlite_cmd.sl_create_tables(sl_cli, './databases/sqlite_db/table_stats_conf.json')
    sl_cli.close()

    # == Récolte ==
    print("== Recolte ==")
    if DEV:
        ds_ham = [os.path.join(os.getcwd(), 'dev_dataset', 'easy_ham')]
        ds_spam = [os.path.join(os.getcwd(), 'dev_dataset', 'spam')]
    else:
        root_ds = '/home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/00_dataset' \
                  '/ds3'
        ds_ham = [os.path.join(root_ds, folder) for folder in ('easy_ham', 'easy_ham_2',
                                                               'hard_ham')]
        ds_spam = [os.path.join(root_ds, folder) for folder in ('spam', 'spam_2')]

    print("-- Création de la liste des fichiers...", end=' ')
    r_data = {'ham': [], 'spam': []}
    for folder in ds_ham:
        r_data['ham'] += mail_load.list_files(folder)
    for folder in ds_spam:
        r_data['spam'] += mail_load.list_files(folder)
    print("OK")

    # - Stats récolte -
    print("--- Process de statistiques après la récole")
    sqlite_cmd.stats_process(sqlite_db, 'recolte', r_data)

    # == Création document ==
    print("== Création document ==")
    n_data = {'spam': create_doc_process('spam', r_data.get('spam', [])),
              'ham': create_doc_process('ham', r_data.get('ham', []))}

    # - Stats create_document
    print("--- Process de statistiques après la création de document")
    sqlite_cmd.stats_process(sqlite_db, 'creation document', n_data)

    # == Mise en base des documents ==
    print("== Mise en base des documents ==")
    # -- ES
    print("-- Création de l'index ElasticSearch...", end=' ')
    es_cli = elastic_cmd.es_connect(es_secrets.serveur,
                                    (es_secrets.apiid, es_secrets.apikey),
                                    es_secrets.ca_cert)
    if not es_cli:
        print("ECHEC connexion ElasticSearch")
        exit(1)

    email_mapping = json.load(open('databases/elastic/mail_mapping.json', 'r'))
    index = "test_import_dev0" if DEV else "import_prod"
    elastic_cmd.es_create_indice(es_cli, index, email_mapping)
    print("OK")

    # -- PSQL
    print("-- Création de la base PostgreSQL")
    psql_cmd.create_user(admin=psql_secrets.admin,
                         adm_pass=psql_secrets.admin_pw,
                         user=psql_secrets.owner,
                         password=psql_secrets.owner_pw,
                         host=psql_secrets.host,
                         port=psql_secrets.port)

    psql_conf = json.load(open("./databases/psql_db/db_mapping.json")) if DEV else json.load(
        open("./databases/psql_db/db_mapping_prod.json"))
    psql_db = list(psql_conf.keys())[0]
    psql_cmd.create_db(nom=psql_db,
                       owner=psql_secrets.owner,
                       user=psql_secrets.admin,
                       passwd=psql_secrets.admin_pw,
                       host=psql_secrets.host,
                       port=psql_secrets.port)

    print("-- Création des tables PostgreSQL...", end=' ')
    psql_conn = psql_cmd.connect_db(database=psql_db,
                                    user=psql_secrets.owner,
                                    passwd=psql_secrets.owner_pw,
                                    host=psql_secrets.host,
                                    port=psql_secrets.port)
    for table in psql_conf[psql_db].keys():
        psql_cmd.create_table(psql_conn, table, psql_conf[psql_db][table])
    print("OK")

    # - Mise en base ES
    for cat in ['spam', 'ham']:
        doublons = 0

        # PSQL Mise en base Categorie
        psql_cmd.insert_data(psql_conn, "categories", {"type": cat})
        id_cat = psql_cmd.get_data(psql_conn,
                                   "categories",
                                   ['id_cat'],
                                   f"type LIKE '{cat}'")[0]['id_cat']

        for document in tqdm.tqdm(n_data.get(cat, []),
                                  desc="-- Mise en base ES & PSQL des {}...".format(cat),
                                  leave=False,
                                  file=sys.stdout,
                                  ascii=True):

            # Séparation des données pour ES et PSQL
            es_document = {key: val for key, val in document.items() if key != "liens"}
            psql_document = {key: val for key, val in document.items() if key in ['hash', 'liens']}

            # Mise en base ES
            if elastic_cmd.es_index_doc(es_cli, index, document):
                doublons += 1
                continue

            # Mise en base PSQL
            psql_cmd.insert_document_init(psql_conn, psql_document, id_cat)

        print("-- Mise en base ES & PSQL des {}... OK ({} doublons)".format(cat, doublons))
    psql_conn.close()

    m_data = {}
    for cat in ['spam', 'ham']:
        print("-- Récupération des {}...".format(cat), end=' ')
        m_data[cat] = elastic_cmd.es_get_all(es_cli,
                                             index,
                                             sort={'hash': 'asc'},
                                             query={"match": {'categorie': cat}})
        print('OK')

    # - Stats mise en base
    print("--- Process de statistiques après la mise en base")
    sqlite_cmd.stats_process(sqlite_db, 'mise en base', m_data)

    es_cli.close()

    print("== FIN ==")

    exit(0)
