#! /usr/bin/env python3
# coding: utf-8

"""
Développement des fonction graphiques
"""

import matplotlib.pyplot as plt


########################################################################################################################
#           Affichage ZIPF                                                                                             #
########################################################################################################################
def show_zipf(titre, dico):
    """
    Affiche la courbe de zipf pour une liste de mots trié
    :param titre:
    :param dico: <list> {"rang": <int>, "mot": <str>, "occurences": <int>
    :return: None
    """
    rang, occurences = zip(*[(info['rang'], info['occurences']) for info in dico])

    plt.figure('Distribution de Zipf')
    plt.plot(rang, occurences, label="réel", c='red')
    plt.title(titre)
    plt.xlabel("rang")
    plt.ylabel("occurences")
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    x = list(range(1, 10))
    y = [c ** 2 for c in x]

    plt.figure('foo')
    plt.plot(x, y, label='carré', lw=1, c='red')
    plt.plot(x, [c**3 for c in x], label="cube")
    plt.title('figure 1')
    plt.xlabel('axe x')
    plt.ylabel('axe y')
    plt.legend()
    plt.show()
    # plt.savefig("save_fig1.png")

    exit(0)
