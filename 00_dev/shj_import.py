#! /usr/bin/env python3
# coding: utf-8

"""
    Module d'importation des mails pour slamhamjam.
"""

# Importations
import sys
import os
import chardet
import csv
from email import message_from_string
from email import policy
import shj_clear as shjc

# Paramètres
csv.field_size_limit(sys.maxsize)

# metadata
__author__ = "Martial GOEHRY"
__licence__ = "GNU GPL v3"
__version__ = "0.0.1"
__status___ = "development"


def list_files(chemin):
    """ Retourne tous les fichiers d'un répertoire recursivement
    :param chemin: <str> - chemin vers le répertoire
    :return: <list> - liste des fichiers
    """
    subdirs = [d[0] for d in os.walk(chemin)]
    files = []

    for sd in subdirs:
        for f in os.listdir(sd):
            x = sd + '/' + f
            if os.path.isfile(x):
                files.append(x)

    return files


def import_from_file(chemin):
    """ Importe un email contenu dans un fichier
    :param chemin: <str> - Chemin vers le fichier
    :return: <email.message.EmailMessage>
    """
    try:
        with open(chemin, 'rb') as data:
            brut = convert(data.read())
            msg = message_from_string(brut, policy=policy.default)

    except FileNotFoundError:
        print("Fichier : '{}' non trouvé".format(chemin), file=sys.stderr)
        return ""

    return msg


def convert(data):
    """ Détecte l'encodage et retourne le message decode
        encodage accepter pour le programme:
            - ascii
            - Windows-1252
            - ISO-8859-1
            - utf-8
    :param data: <str>
    :return: <str>
    """
    codings = ['ascii', 'Windows-1252', 'ISO-8859-1', 'utf-8']
    charset = chardet.detect(data).get('encoding')

    if charset not in codings:
        return ""

    return data.decode(charset)


def extract_meta(msg):
    """ Extrait les metadonnées d'un message
    :param msg: <email.message.EmailMessage>
    :return: <list>
    """
    sujet = msg.get('Subject')
    expediteur = msg.get('From', 'Inconnu').replace("'", "''")
    return sujet, expediteur


def extract_body(msg):
    """ Extraire le corps du mail
    :param msg: <email.message.EmailMessage> Mail
    :return:
    """
    refused_charset = ['unknown-8bit', 'default', 'default_charset',
                       'gb2312_charset', 'chinesebig5', 'big5']
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if not part.is_multipart():
                body += extract_body(part)
        return body

    if msg.get_content_maintype() != 'text':
        return ""

    if msg.get_content_charset() in refused_charset:
        return ""

    if msg.get_content_subtype() == 'plain':
        payload = msg.get_payload(decode=True)
        body += payload.decode(errors='ignore')

    if msg.get_content_subtype() == 'html':
        payload = msg.get_payload(decode=True)
        body += shjc.clear_html(payload.decode(errors='ignore'))

    if msg.get_content_subtype() == 'enriched':
        payload = msg.get_payload(decode=True)
        body += shjc.clear_enriched(payload.decode(errors='ignore'))

    return body


def import_from_csv(chemin):
    """ Importe tous les messages d'un fichier CSV
    :param chemin: <str> chemin vers le fichier CSV
    :return: <list> [fichier <str>, message <email.message.EmailMessage>]
    """
    data = []
    with open(chemin, newline='') as csvfile:
        lect = csv.reader(csvfile)
        for ligne in lect:
            fichier = ligne[0]
            message = message_from_string(ligne[1])
            data.append([fichier, message])
    return data


if __name__ == '__main__':
    # import from csv
    data = import_from_csv("./data/csv/emails.csv")[1:]
    print(len(data))
    print(data[1])
    exit(0)

    debug = 0
    if debug:
        file = './data/spam_2/00959.016c91a5c76f15d7f67b01a24645b624'
        message = import_from_file(file)
        corp = extract_body(message)
        corp = shjc.clear_texte(corp)
        sujet, exp = extract_meta(message)
        print(exp)
        exit(0)

    for file in list_files("./data/"):
        message = import_from_file(file)
        sujet, exp = extract_meta(message)
        print(exp)

    exit(0)
