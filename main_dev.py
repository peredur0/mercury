#! /usr/bin/env python3
# coding: utf-8

"""
    Main de développement avec peu de mail à charger
"""

import os
import platform
import warnings
# import magic
import langdetect
from importation import mail_load
from traitement import text_pre_clear, text_traitement

#######################################################################################################################
#           Importation des fichiers                                                                                  #
#######################################################################################################################
current_os = platform.system().lower()
root = os.getcwd()

ds_ham = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'easy_ham'])
ds_spam = root + "{}".format('\\' if current_os == 'windows' else '/').join(['', 'dev_dataset', 'spam'])

liste_ham = mail_load.list_files(ds_ham)
liste_spam = mail_load.list_files(ds_spam)


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
def pretraitement(data, categorie):
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
    corp, liens = text_pre_clear.clear_texte(corp)
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
        'categorie': categorie.lower(),
        'sujet': sujet,
        'expediteur': expediteur,
        'message': corp,
        'langue': lang,
        'liens': liens,
        'nb_mots': len(mots),
        'nb_occurences': len(set(mots))
    }
    return document


#######################################################################################################################
#           Dev main                                                                                                  #
#######################################################################################################################
if __name__ == '__main__':
    warnings.filterwarnings('ignore')

    print("{} fichiers dans liste_ham".format(len(liste_ham)))
    print("{} fichiers dans liste_spam".format(len(liste_spam)))

    docs_spam = []
    rej_spam = []
    for fichier in liste_spam:
        messages = importation(fichier)
        if not messages:
            rej_spam.append(fichier)
            continue

        for message in messages:
            m_doc = pretraitement(message, 'spam')
            docs_spam.append(m_doc) if m_doc else rej_spam.append(fichier)

    print("*" * 80)
    print("{} document dans liste_spam".format(len(docs_spam)))
    print("{} fichier spam rejeté".format(len(rej_spam)))

    docs_ham = []
    rej_ham = []
    for fichier in liste_ham:
        messages = importation(fichier)
        if not messages:
            rej_ham.append(fichier)
            continue

        for message in messages:
            m_doc = pretraitement(message, 'ham')
            docs_ham.append(m_doc) if m_doc else rej_ham.append(fichier)

    print("*" * 80)
    print("{} document dans liste_ham".format(len(docs_ham)))
    print("{} fichier ham rejeté".format(len(rej_ham)))

    exit(0)
