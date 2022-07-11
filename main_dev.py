#! /usr/bin/env python3
# coding: utf-8

"""
    Main de développement avec peu de mail à charger
"""

import os
import magic
from importation import mail_load
from nettoyage import text_clear

ds_ham = "/home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/00_dataset/dev_dataset/easy_ham"
ds_spam = "/home/perceval/LicenceIED/01_exercices-en-cours/L3_C1-15_Projet/V2/00_dataset/dev_dataset/spam"

#######################################################################################################################
#           Importation des fichiers                                                                                  #
#######################################################################################################################
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

    if magic.from_file(chemin, mime=True) == 'application/csv':
        return mail_load.import_from_csv(chemin)

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
    nettoyage sommaire du message
    gestion de la catégorie de mail
    ajout de données chiffrées
    :param data: (<str>, <email.message.EmailMessage>)
    :param categorie: <str> categorie de mail: ham, spam, ou inconnu
    :return: <>
    """
    chemin, mail = data
    corp = mail_load.extract_body(mail)
    corp, liens = text_clear.clear_texte(corp)
    sujet, expediteur = mail_load.extract_meta(mail)

    mots = [mot for mot in corp.split(' ') if len(mot) > 0]

    if categorie.lower() not in ['spam', 'ham']:
        categorie = 'inconnu'

    document = {
        'chemin': chemin,
        'categorie': categorie.lower(),
        'sujet': sujet,
        'expediteur': expediteur,
        'message': corp,
        'liens': liens,
        'nb_mots': len(mots),
        'nb_occurences': len(set(mots))
    }
    return document


#######################################################################################################################
#           Dev main                                                                                                  #
#######################################################################################################################
if __name__ == '__main__':
    print("{} fichiers dans liste_ham".format(len(liste_ham)))
    print("{} fichiers dans liste_spam".format(len(liste_spam)))

    liste_doc = []
    rejected = []
    for fichier in liste_spam:
        data_imp = importation(fichier)
        if not data_imp:
            rejected.append(fichier)
            continue

        for d in data_imp:
            liste_doc.append(pretraitement(d, 'spam'))

    print("{} document dans liste_spam".format(len(liste_doc)))
    print("{} fichier rejeté".format(len(rejected)))

    for doc in liste_doc:
        print(doc)

    exit(0)

    # Utiliser pour lister les chardet non anglophone
    import chardet
    for file in rejected:
        with open(file, 'rb') as data:
            print('{} : {}'.format(chardet.detect(data.read()).get('encoding'), file))

