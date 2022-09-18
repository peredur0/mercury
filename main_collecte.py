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
    if not mail:
        return None

    return [(chemin, mail)]


#######################################################################################################################
#           Création du document                                                                                      #
#######################################################################################################################
def create_document(data, categorie):
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
    corp, liens = nettoyage.clear_texte_init(corp)
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


def create_doc_process(categorie, liste):
    """
    Porcessus de création de document avec une barre de progression nested
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
        stats_dict["mots"] += doc["nb_mots"]

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
        stats_dict["mots"] += doc["_source"]["nb_mots"]
        for mot in doc["_source"]["message"].split():
            if mot not in m_uniq:
                m_uniq.append(mot)

    stats_dict["mots_uniques"] = len(m_uniq)
    stats_dict["mails"] = len(liste)
    stats_dict["etape"] = "mise en base"

    print("-- Stats - étape : Mise en base {}... OK".format(categorie))
    return m_uniq


def stats_process(etape, data):
    """
    Gère le processus de récolte et d'affichage des statistique pour chaque étape
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
    sl_cli = sqlite_cmd.sl_connect('./databases/sqlite_db/stats_dev.db')

    print("--- Sauvegarde des stats de l'étape: {}...".format(etape), end=' ')
    sqlite_cmd.sl_insert(sl_cli, 'globales', stats_globales)
    sqlite_cmd.sl_insert(sl_cli, 'ham', stats_ham)
    sqlite_cmd.sl_insert(sl_cli, 'spam', stats_spam)
    print('OK')

    print("Données stats de l'étape: {}:".format(etape))
    for cat in ['ham', 'spam', 'globales']:
        print_stats(cat, etape, sl_cli)

    sl_cli.close()
    return


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
    index = "test_import_all0"
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
