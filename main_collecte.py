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
#           Nettoyage                                                                                                 #
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


def nettoyage_process(categorie, liste):
    """
    Porcessus de nettoyage avec une barre de progression nested
    :param categorie: <str> Catégorie de mail, Ham ou Spam
    :param liste: <list> liste de
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
                                     desc="Nettoyage {}".format(messages[0][0].split('/')[-1]),
                                     leave=False,
                                     ascii=True,
                                     file=sys.stdout):
                m_doc = nettoyage(message, categorie)
                if m_doc:
                    docs.append(m_doc)
    print("-- Importation - Nettoyage {}... OK".format(categorie))
    return docs


#######################################################################################################################
#           Statistiques                                                                                              #
#######################################################################################################################
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


def stats_nettoyage(categorie, stats_dict, liste):
    """
    Récupération des infos statistiques après nettoyage
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
        stats_dict["mots"] += doc["nb_mots"]

        for mot in doc["message"].split():
            if mot not in m_uniq:
                m_uniq.append(mot)

    stats_dict["mots_uniques"] = len(m_uniq)
    stats_dict["mails"] = len(liste)
    stats_dict["etape"] = "nettoyage"

    print("-- Stats - étape : Nettoyage {}... OK".format(categorie))
    return m_uniq


#######################################################################################################################
#           Dev main                                                                                                  #
#######################################################################################################################
if __name__ == '__main__':
    warnings.filterwarnings('ignore')

    print("== Création de la base SQLITE")
    sl_cli = sqlite_cmd.sl_connect('./databases/sqlite_db/stats_dev.db')
    sqlite_cmd.sl_create_tables(sl_cli, './databases/sqlite_db/table_stats_conf.json')
    sl_cli.close()

    stats_temp = {
        'etape': 'template',
        'mails': 0,
        'mots': 0,
        'mots_uniques': 0
    }

    # == Récolte ==
    print("== Recolte ==")
    current_os = platform.system().lower()
    root = os.getcwd()

    ds_ham = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'easy_ham'])
    ds_spam = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'spam'])

    print("-- Création de la liste des fichiers...", end=' ')
    liste_ham = mail_load.list_files(ds_ham)
    liste_spam = mail_load.list_files(ds_spam)
    print("OK")

    # - Stats récolte -
    # Données pour SQLite
    stats_spam = stats_temp.copy()
    stats_ham = stats_temp.copy()
    stats_globales = stats_temp.copy()

    uniq_spam = stats_recolte('spam', stats_spam, liste_spam)
    uniq_ham = stats_recolte('ham', stats_ham, liste_ham)

    stats_globales['mails'] = stats_spam.get('mails', 0) + stats_ham.get('mails', 0)
    stats_globales['mots'] = stats_spam.get('mots', 0) + stats_ham.get('mots', 0)
    stats_globales['mots_uniques'] = len(set(uniq_ham + uniq_spam))
    stats_globales['etape'] = "recolte"

    # - Mise en base : statistiques de la récolte
    sl_cli = sqlite_cmd.sl_connect('./databases/sqlite_db/stats_dev.db')

    print("--- Sauvegarde des stats de la récolte...", end=' ')
    sqlite_cmd.sl_insert(sl_cli, 'globales', stats_globales)
    sqlite_cmd.sl_insert(sl_cli, 'ham', stats_ham)
    sqlite_cmd.sl_insert(sl_cli, 'spam', stats_spam)
    print('OK')

    print("Données stats de la récolte:")
    for cat in ['ham', 'spam', 'globales']:
        print_stats(cat, "recolte", sl_cli)

    sl_cli.close()

    # == Nettoyage ==
    stats_spam = stats_temp.copy()
    stats_ham = stats_temp.copy()
    stats_globales = stats_temp.copy()

    print("== Nettoyage ==")
    docs_spam = nettoyage_process('spam', liste_spam)
    docs_ham = nettoyage_process('ham', liste_ham)

    # - Mise en base : statistiques de la récolte
    # Données pour SQLite
    uniq_spam = stats_nettoyage('spam', stats_spam, docs_spam)
    uniq_ham = stats_nettoyage('ham', stats_ham, docs_ham)

    stats_globales['mails'] = stats_spam.get('mails', 0) + stats_ham.get('mails', 0)
    stats_globales['mots'] = stats_spam.get('mots', 0) + stats_ham.get('mots', 0)
    stats_globales['mots_uniques'] = len(set(uniq_ham + uniq_spam))
    stats_globales['etape'] = "nettoyage"

    sl_cli = sqlite_cmd.sl_connect('./databases/sqlite_db/stats_dev.db')
    print("--- Sauvegarde des stats du nettoyage...", end=' ')
    sqlite_cmd.sl_insert(sl_cli, 'spam', stats_spam)
    sqlite_cmd.sl_insert(sl_cli, 'ham', stats_ham)
    sqlite_cmd.sl_insert(sl_cli, 'globales', stats_globales)
    print('OK')

    print("Données stats du nettoyage:")
    for cat in ['ham', 'spam', 'globales']:
        print_stats(cat, "nettoyage", sl_cli)

    sl_cli.close()

    # == Mise en base des documents ==
    print("== Mise en base des documents ==")
    print("-- Création de l'index ElasticSearch...", end=' ')
    es_cli = elastic_cmd.es_connect(secrets.serveur, (secrets.apiid, secrets.apikey), secrets.ca_cert)
    if not es_cli:
        print("ECHEC")
        exit(1)

    email_mapping = json.load(open('databases/elastic_docker/mail_mapping.json', 'r'))
    index = "test_import_all0"
    elastic_cmd.es_create_indice(es_cli, index, email_mapping)
    print("OK")

    # - Mise en base
    for document in tqdm.tqdm(docs_spam, desc="-- Mise en base SPAM...", leave=False, file=sys.stdout, ascii=True):
        elastic_cmd.es_index_doc(es_cli, index, document)
    print("-- Mise en base SPAM... OK")

    for document in tqdm.tqdm(docs_ham, desc="-- Mise en base HAM...", leave=False, file=sys.stdout, ascii=True):
        elastic_cmd.es_index_doc(es_cli, index, document)
    print("-- Mise en base HAM... OK")

    es_cli.close()

    # Récupération des statistiques après mise en base




    print("== FIN ==")

    exit(0)
