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
        - travail graphique
"""


########################################################################################################################
#             Statistiques / Probabilités                                                                              #
########################################################################################################################
import re


def frequence_mot(bag):
    """
    calcule la fréquence de chaque mot dans un sac de mot
    :param bag: <list> - liste de tous les mots d'un texte
    :return: <dict> - dictionnaire avec la fréquence par mot
    """
    freq = {}
    for mot in bag:
        if mot in freq.keys():
            freq[mot] += 1
        else:
            freq[mot] = 1

    return freq


def classement_freq(dico):
    """
    Trie un dictionnaire de mots : occurence et leur assigne un rang en fonction du nombre d'occurence
    :param dico: <dict> dictionnaire de mot: occurences
    :return: <list> {"rang": <int>, "mot": <str>, "occurences": <int>}
    """
    ranked = []
    for rang, couple in enumerate(sorted(dico.items(), key=lambda item: item[1], reverse=True), start=1):
        ranked.append({"rang": rang, "mot": couple[0], "occurences": couple[1]})

    return ranked


def freq_zipf(nb_mots, rang, s):
    """
    Retourne la fréquence théorique d'un mot selon la loi de distribution de zipf
    # help : https://iq.opengenus.org/zipfs-law/
    # help : https://www.youtube.com/watch?v=WYO8Rc4JB_Y
    # todo: développer encore
    :param nb_mots: <int> nombre d'occurence du mot le plus fréquent
    :param rang: <int> rang du mot à déterminer
    :param s: <float> environ 1
    :return: <float> nombre d'occurence estimée
    """
    return 1


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
    import traitement.graphs as graphs
    import nltk
    from nltk.corpus import brown, stopwords

    # Développement de la fonction zipf
    nltk.download("brown")
    stopsw = set(stopwords.words('english'))

    # Nettoyage basic
    print("longeur brown.words() :", len(brown.words()))
    freq_b = frequence_mot([mot.lower() for mot in brown.words() if re.match(r'\w+', mot)])
    freq_b2 = frequence_mot([mot.lower() for mot in brown.words() if (re.match(r'\w+', mot)) and (mot not in stopsw)])

    print("nombres de mots", len(freq_b.keys()))
    sort_b = classement_freq(freq_b)

    for info in sort_b[:5]:
        print("{}\t{}\t{}".format(info['occurences'], info['rang'], info['mot']))

    graphs.show_zipf("Brown", sort_b)

    exit(0)
