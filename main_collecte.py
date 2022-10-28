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
from databases import elastic_cmd, sqlite_cmd
from databases.elastic import secrets


warnings.filterwarnings('ignore')


#######################################################################################################################
#           Importation des fichiers                                                                                  #
#######################################################################################################################
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


#######################################################################################################################
#           Création du document                                                                                      #
#######################################################################################################################
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
        messages = importation(fichier)
        if messages:
            for message in tqdm.tqdm(messages,
                                     desc="Création {}".format(messages[0][0].split('/')[-1]),
                                     leave=False,
                                     ascii=True,
                                     file=sys.stdout):
                m_doc = create_document(message, categorie)
                if m_doc:
                    docs.append(m_doc)
    print("-- Importation - Création {}... OK".format(categorie))
    return docs


#######################################################################################################################
#           Mise en place des bases de données                                                                        #
#######################################################################################################################
def bdd_init_es():
    """
    Initialisation de l'index ElasticSearch.
    Stockage des corps des mails avec le minimum de traitement.
    :return:
    """
    pass


def bdd_init_psql():
    """
    Initialisation de la base de données PostgreSQL
    Stockage des features et données générées.
    :return:
    """
    pass


def bdd_init_sqlite():
    """
    Initialisation de base de donnees SQLite
    Stockage des informations statistiques lors des étapes du traitement.
    :return:
    """
    pass


#######################################################################################################################
#          Phase 1: collecte et mise en base                                                                          #
#######################################################################################################################
if __name__ == '__main__':
    print("=== Phase 1 : collecte & mise en base ===")
    print("== Création de la base SQLITE")
    sl_cli = sqlite_cmd.sl_connect('./databases/sqlite_db/stats_dev.db')
    sqlite_cmd.sl_create_tables(sl_cli, './databases/sqlite_db/table_stats_conf.json')
    sl_cli.close()

    # == Récolte ==
    print("== Recolte ==")
    current_os = platform.system().lower()
    root = os.getcwd()
    ds_ham = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'easy_ham'])
    ds_spam = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'spam'])

    print("-- Création de la liste des fichiers...", end=' ')
    r_data = {'ham': mail_load.list_files(ds_ham),
              'spam': mail_load.list_files(ds_spam)}
    print("OK")

    # - Stats récolte -
    print("--- Process de statistiques après la récole")
    stats_process('recolte', r_data)

    # == Création document ==
    print("== Création document ==")
    n_data = {'spam': create_doc_process('spam', r_data.get('spam', [])),
              'ham': create_doc_process('ham', r_data.get('ham', []))}

    # - Stats create_document
    print("--- Process de statistiques après la création de document")
    stats_process('creation document', n_data)

    # == Mise en base des documents ==
    print("== Mise en base des documents ==")
    print("-- Création de l'index ElasticSearch...", end=' ')
    es_cli = elastic_cmd.es_connect(secrets.serveur, (secrets.apiid, secrets.apikey), secrets.ca_cert)
    if not es_cli:
        print("ECHEC connexion ElasticSearch")
        exit(1)

    email_mapping = json.load(open('databases/elastic/mail_mapping.json', 'r'))
    index = "test_import_dev0"
    elastic_cmd.es_create_indice(es_cli, index, email_mapping)
    print("OK")

    # - Mise en base
    for cat in ['spam', 'ham']:
        doublons = 0
        for document in tqdm.tqdm(n_data.get(cat, []),
                                  desc="-- Mise en base des {}...".format(cat),
                                  leave=False,
                                  file=sys.stdout,
                                  ascii=True):
            doublons += elastic_cmd.es_index_doc(es_cli, index, document)
        print("-- Mise en base des {}... OK ({} doublons)".format(cat, doublons))

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
    stats_process('mise en base', m_data)

    es_cli.close()

    print("== FIN ==")

    exit(0)
