#! /usr/bin/env python3
# coding: utf-8

"""
    Module d'exploitation:
        - traitement NLP
            - nltk - tokenisation, POS tagging,  lemmatisation, stopwords
            - Standford - tokenisation, POS tagging, lemmatisation, noms propres
            - calcul de la distribution des tag.

        - travail sur la fréquence des mots
            * récupération de la fréquence pour les mots d'un texte
            * loi de Zipf
                - calculer le nombre d'occurences théorique par mot selon son rang
                - calculer l'écart entre le nombre d'occurence théorique et la réalité du texte
                    (sur tout le texte ou sur une partie restreinte)
            * Proprotion d'Harax
                - calculer le pourcentage de mot n'ayant qu'une seule occurence

        - travail sur le nombre de faute
        - travail sur les thèmes
            (SOM)
"""


import sys
import numpy as np
import matplotlib.pyplot as plt


########################################################################################################################
#             Statistiques / Probabilités                                                                              #
########################################################################################################################
def frequence_mot(bag):
    """
    calcule la fréquence de chaque mot dans un sac de mot
    :param bag: <list> - liste de tous les mots d'un texte
    :return: <dict> - dictionnaire avec la fréquence par mot {mot: frequence}
    """
    freq = {}
    for mot in bag:
        if mot in freq.keys():
            freq[mot] += 1
        else:
            freq[mot] = 1

    return freq


def cout(l1, l2, methode):
    """
    Calcul le cout de l'écart entre les éléments de l1 et le l2, place par place
    :param l1: <list> liste d'entier
    :param l2: <liste> liste d'entier
    :param methode: <str> méthode de calcul du cout
    :return: <float> cout selon méthode
    """
    ls_cout = [abs(x - y) for x, y in zip(l1, l2)]

    if methode.lower() not in ['moyenne', 'somme']:
        print("Erreur, fonction cout - methode '{}' inconnue".format(methode), file=sys.stderr)
        return None

    if methode.lower() == 'moyenne':
        if len(ls_cout) == 0:
            print("Erreur, fonction cout - division par zéro pour la moyenne", file=sys.stderr)
            return None
        return np.average(ls_cout)

    if methode.lower() == 'somme':
        return sum(ls_cout)

    return None


def classement_zipf(dico):
    """
    Trie un dictionnaire de mots : occurence et leur assigne un rang en fonction du nombre d'occurence
    :param dico: <dict> dictionnaire de mot: occurences
    :return: <list> {"rang": <int>, "mot": <str>, "frequence": <int>}
    """
    ranked = []
    for rang, couple in enumerate(sorted(dico.items(), key=lambda item: item[1], reverse=True), start=1):
        ranked.append({"rang": rang,
                       "mot": couple[0],
                       "frequence": couple[1]})

    return ranked


def zipf_process(sorted_list):
    """

    :param sorted_list: <list> liste ordonnée des mots selon leur rang
                        {"rang": <int>, "mot": <str>, "frequence": <int>
    :return: <tuple> (<float> - coef, <int?> cout)
    """
    # Calcul de la moyenne(frequence x rang) = constante
    constante = np.average([elem['rang'] * elem['frequence'] for elem in sorted_list])

    # Déterminer le meilleur coeficiant
    rang = [elem['rang'] for elem in sorted_list]              # dev recherche minimum
    freq_reel = [elem['frequence'] for elem in sorted_list]


    # plt développement
    plt.figure("recherche minimum", figsize=(10, 10))

    ls_coef = list(np.arange(0.8, 1.5, 0.01))
    cout_moy = []
    cout_sum =
    for coef in ls_coef:
        freq_theo = [zipf_freq_theorique(constante, x, coef) for x in range(1, len(freq_reel)+1)]
        cout_moy.append(cout(freq_reel, freq_theo, 'moyenne'))

    plt.plot(ls_coef, cout_moy, label="moyenne", c='black')
    plt.xlabel('coef')
    plt.ylabel('cout')
    plt.legend()
    plt.show()


def zipf_freq_theorique(constante, rang, coef):
    """
    Calcul la fréquence théorique d'un mot selon son rang, la constante du texte et un coeficiant d'ajustement
    :param constante: <int> constante déterminer par la distribution de Zipf
    :param rang: <int> rang du mot selon sa fréquence
    :param coef: <float> variable d'ajustement
    :return: <float> fréquence théorique zipfienne
    """
    return constante / (rang ** coef)


########################################################################################################################
#             NLP processing                                                                                           #
########################################################################################################################
def nlp_process(texte, method):
    """
    Passe un texte à travers travers une méthode de nlp
    :param texte: <str> texte à travailler
    :param method <str> methode à utiliser pour le traitement
    :return: <list> liste de tous les mots encore présent après le traitement nlp
    """
    return


if __name__ == '__main__':
    import re
    import nltk
    from nltk.corpus import brown, stopwords

    # Développement de la fonction zipf
    nltk.download("brown")
    nltk.download("stopwords")
    stopsw = set(stopwords.words('english'))

    # Nettoyage basic
    print("longeur brown.words() :", len(brown.words()))
    freq_b = frequence_mot([mot.lower() for mot in brown.words() if re.match(r'\w+', mot)])

    print("nombres de mots", len(freq_b.keys()))
    sort_b = classement_zipf(freq_b)

    zipf_process(sort_b)

    exit(0)

    for info in sort_b[:5]:
        print(info)

    r, f = zip(*[(i['rang'], i["frequence"]) for i in sort_b])

    plt.figure("Distribution", figsize=(5, 5))
    plt.scatter(r, f, label="réel", marker='+', c='black')
    plt.xlabel('rang')
    plt.ylabel('fréquence')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.show()

    exit(0)
