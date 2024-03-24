#! /usr/bin/env python3
# coding: utf-8

"""
    Module pour la lemminisation des mails

          Lemminisation
            - retrait et decompte des substitution (LIEN, TEL, NOMBRE, PRIX, ...)
            - lemminisation des mots
"""

# Importation
import re
import nltk
from nltk.corpus import stopwords

# metadata
__author__ = "Martial GOEHRY"
__licence__ = "GNU GPL v3"
__version__ = "0.0.0"
__status___ = "development"

# globales
cles = ['URL', 'MAIL', 'TEL', 'NOMBRE', 'PRIX']


def extrait_subst(texte, subst):
    """ Extrait les substitutions et compte les occurences
        :global cles: <list>, cle de substitution
    :param texte: <str>
    :param subst: <dict>
    :return: <str> texte moins les substitutions
    """
    for c in cles:
        subst[c] = 0

    for mot in texte.split(" "):
        if mot in subst:
            subst[mot] += 1

    for c in cles:
        texte = re.sub(c, '', texte)

    return texte


def extrait_lem(texte, lem):
    """ Effectue une lemminisation du texte et stocke les occurences
    :param texte: <str>
    :param lem: <dict>
    :return: <int> nombre de mot du texte
    """
    nb = 0
    mots = nltk.word_tokenize(texte)

    for mot in mots:
        if mot == '\x00':           # Non supporter par Postgres
            continue

        if mot in lem:
            lem[mot] += 1
        else:
            lem[mot] = 1
        nb += 1

    return nb


if __name__ == '__main__':
    nltk.download('wordnet')
    nltk.download('punkt')
    nltk.download('stopwords')

    message = "hello adam, how are you? i hope everything is going well. today is a good day, see you dude."
    stpword = stopwords.words('english')

    message = extrait_subst(message, {})
    mots = nltk.word_tokenize(message)
    print(mots)
    for mot in mots:
        if mot in stpword:
            mots.remove(mot)
    print(mots)
    freq = nltk.FreqDist(mots)

    print(freq.items())

    for mot, occ in freq.items():
        print(mot, ':', occ)

    exit(0)
