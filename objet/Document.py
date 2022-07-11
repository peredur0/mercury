#! /usr/bin/env python3
# coding: utf-8

"""
   Objet Document:
     Regroupe toutes les informations du mails pour la mise en base
     - hash - md5
     - chemin - chemin d'accès au fichier
     - catégorie - spam ou ham
     - sujet - objet du mail
     - message - corps du texte
     - nombre de mots - nombre de mots uniques dans le mail avant traitement
     - nombre d'occurences - quantité totale des mots dans le message
     - nombres liens - URL / MAIL / TEL / NOMBRE / PRIX
"""


class Document:
    """
    Classe regroupant les informations utile des mails.
    Liste des attributs:
        -
    """
