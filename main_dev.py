#! /usr/bin/env python3
# coding: utf-8

"""
    Main de développement avec peu de mail à charger
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
from traitement import nettoyage_init
from databases import elastic_cmd, sqlite_cmd
from databases.elastic_docker import secrets


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
    if not mail:
        return None

    return [(chemin, mail)]


#######################################################################################################################
#           Prétraitement                                                                                             #
#######################################################################################################################
def nettoyage(data, categorie):
    """
    extraction du message
    récupération des métadonnées
    traitement sommaire du message
    gestion de la catégorie de mail
    ajout de données chiffrées
    filtrage de la langue
    :param data: (<str>, <email.message.EmailMessage>)
    :param categorie: <str> categorie de mail: ham, spam, ou inconnu
    :return: <dict>
    """
    chemin, mail = data
    corp = mail_load.extract_body(mail)
    corp, liens = nettoyage_init.clear_texte(corp)
    sujet, expediteur = mail_load.extract_meta(mail)

    try:
        lang = langdetect.detect(corp)
    except langdetect.lang_detect_exception.LangDetectException:
        return None

    if lang != 'en':
        return None

    mots = [mot for mot in corp.split(' ') if len(mot) > 0]

    if categorie.lower() not in ['spam', 'ham']:
        categorie = 'inconnu'

    document = {
        'chemin': chemin,
        'hash': hashlib.md5(corp.encode()).hexdigest(),
        'categorie': categorie.lower(),
        'sujet': sujet,
        'expediteur': expediteur,
        'message': corp,
        'langue': lang,
        'liens': liens,
        'nb_mots': len(mots),
        'nb_mots_uniques': len(set(mots))
    }
    return document


#######################################################################################################################
#           Dev main                                                                                                  #
#######################################################################################################################
if __name__ == '__main__':
    warnings.filterwarnings('ignore')

    # Données pour SQLite
    stats_spam = {
        'mails': 0,
        'mots': 0,
        'mots_uniques': 0
    }
    stats_ham = {
        'mails': 0,
        'mots': 0,
        'mots_uniques': 0
    }
    stats_globales = {
        'mails': 0,
        'mots': 0,
        'mots_uniques': 0
    }

    # == Récolte ==
    current_os = platform.system().lower()
    root = os.getcwd()

    ds_ham = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'easy_ham'])
    ds_spam = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'spam'])

    print("-- Création de la liste des fichiers...", end=' ')
    liste_ham = mail_load.list_files(ds_ham)
    liste_spam = mail_load.list_files(ds_spam)
    print("OK")

    # - SPAM -
    uniq_spam = []
    for file in tqdm.tqdm(liste_spam, desc="-- Récolte mots et uniques dans SPAM...", leave=False, file=sys.stdout):
        try:
            mots = open(file, 'r').read().split()
            stats_spam['mots'] += len(mots)
            for mot in mots:
                if mot not in uniq_spam:
                    uniq_spam.append(mot)
        except UnicodeDecodeError:
            continue
    stats_spam['mots_uniques'] = len(uniq_spam)

    print("-- Récolte mots et uniques dans SPAM... OK")

    # - HAM -
    uniq_ham = []
    for file in tqdm.tqdm(liste_ham, desc="-- Récolte mots et uniques dans HAM...", leave=False, file=sys.stdout):
        try:
            mots = open(file, 'r').read().split()
            stats_ham['mots'] += len(mots)
            for mot in mots:
                if mot not in uniq_ham:
                    uniq_ham.append(mot)
        except UnicodeDecodeError:
            continue
    stats_ham['mots_uniques'] = len(uniq_ham)

    print("-- Récolte mots et uniques dans HAM... OK")

    stats_spam['mails'] = len(liste_spam)
    stats_ham['mails'] = len(liste_ham)
    uniq = set(uniq_ham + uniq_spam)

    stats_globales['mails'] = stats_spam.get('mails', 0) + stats_ham.get('mails', 0)
    stats_globales['mots'] = stats_spam.get('mots', 0) + stats_ham.get('mots', 0)
    stats_globales['mots_uniques'] = len(uniq)

    print("-- Création de la base SQLITE")
    # - Mise en base : statistiques de la récolte
    sl_cli = sqlite_cmd.sl_connect('./databases/sqlite_db/stats_dev.db')
    sqlite_cmd.sl_create_tables(sl_cli, './databases/sqlite_db/table_stats_conf.json')

    stats_globales['etape'] = 'recolte'
    stats_ham['etape'] = 'recolte'
    stats_spam['etape'] = 'recolte'

    print("--- Mise en base des stats de récolte...", end=' ')
    sqlite_cmd.sl_insert(sl_cli, 'globales', stats_globales)
    sqlite_cmd.sl_insert(sl_cli, 'ham', stats_ham)
    sqlite_cmd.sl_insert(sl_cli, 'spam', stats_spam)
    print('OK')

    print("Données de la récolte:")
    for cat in ['ham', 'spam', 'globales']:
        print('\t{}:'.format(cat.upper()))
        cursor = sl_cli.execute("SELECT mails, mots, mots_uniques "
                                "FROM {} "
                                "WHERE etape LIKE '{}';".format(cat, 'recolte'))
        ligne1 = cursor.fetchone()
        if len(ligne1) != 3 or not ligne1:
            print("Error :", ligne1)

        print('mails: {} \tmots: {}\t mots uniques: {}'.format(ligne1[0], ligne1[1], ligne1[2]))

    sl_cli.close()

    exit(0)

    # == Nettoyage ==
    docs_spam = []
    rej_spam = []

    # - SPAM -
    for fichier in liste_spam:
        messages = importation(fichier)
        if not messages:
            rej_spam.append(fichier)
            continue

        for message in messages:
            m_doc = nettoyage(message, 'spam')
            docs_spam.append(m_doc) if m_doc else rej_spam.append(fichier)

    print("*" * 80)
    print("{} document dans liste_spam".format(len(docs_spam)))
    print("{} fichier spam rejeté".format(len(rej_spam)))

    print("*" * 80)
    print("Mise en base")

    es_cli = elastic_cmd.es_connect(secrets.serveur, (secrets.apiid, secrets.apikey), secrets.ca_cert)
    if not es_cli:
        exit(1)

    email_mapping = json.load(open('databases/elastic_docker/mail_mapping.json', 'r'))
    index = "test_import_spam0"

    elastic_cmd.es_create_indice(es_cli, index, email_mapping)

    for document in docs_spam:
        elastic_cmd.es_index_doc(es_cli, index, document)

    es_cli.close()

    ##
    exit(0)
    ##

    docs_ham = []
    rej_ham = []
    for fichier in liste_ham:
        messages = importation(fichier)
        if not messages:
            rej_ham.append(fichier)
            continue

        for message in messages:
            m_doc = nettoyage(message, 'ham')
            docs_ham.append(m_doc) if m_doc else rej_ham.append(fichier)

    print("*" * 80)
    print("{} document dans liste_ham".format(len(docs_ham)))
    print("{} fichier ham rejeté".format(len(rej_ham)))

    exit(0)
