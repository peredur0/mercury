#! /usr/bin/env python3
# coding: utf-8

"""
Développement des fonctions graphiques
"""

import matplotlib.pyplot as plt


####################################################################################################
#           Affichage ZIPF                                                                         #
####################################################################################################
def show_zipf_stat(zipf_data, rang, frequence, cout_p_coef, freq_theo_min):
    """
    Affiche les données de la distribution de zipf
    :param zipf_data: <dict> dictionnaire avec les données de l'analyse zipf
    :param rang: <list> liste avec tous les rangs de mots
    :param frequence: <list> liste des fréquences pour chaque rang
    :param cout_p_coef: <dict> dictionnaire des couts par coeficients
    :param freq_theo_min: <list> liste des fréquences théoriques pour la coef avec le cout le plus bas
    :return: None
    """
    ligne = 1
    colonne = 4
    position = 1

    fig = plt.figure("Données de la distribution de Zipf", figsize=(17, 5))
    fig.subplots_adjust(wspace=0.3)

    plt.subplot(ligne, colonne, position, title="Distribution brute")
    plt.scatter(rang, frequence, label="réel", marker='+', c='black')
    plt.ylabel('fréquence')
    plt.xlabel('rang')
    plt.yscale('log')
    plt.xscale('log')
    plt.legend()
    position += 1

    plt.subplot(ligne, colonne, position, title="Estimation de la constante")
    plt.plot(rang, [e[0] * e[1] for e in zip(rang, frequence)], label="rang x fréquence", c='black')
    plt.plot(rang, [zipf_data['const_moy']] * (len(rang)), label="constante moyenne", c='blue')
    plt.ylabel('constante estimée')
    plt.xlabel('rang')
    plt.yscale('log')
    plt.xscale('log')
    plt.legend()
    position += 1

    plt.subplot(ligne, colonne, position, title="Cout absolu selon coef")
    plt.plot(list(cout_p_coef.keys()), list(cout_p_coef.values()), label='cout', c='black')
    plt.plot(list(cout_p_coef.keys()), [zipf_data['cout_min']] * len(cout_p_coef), label='cout minimum', c='blue')
    plt.ylabel('cout absolu')
    plt.xlabel('coefficent')
    plt.legend()
    position += 1

    plt.subplot(ligne, colonne, position, title="Distribution avec estimation")
    plt.scatter(rang, frequence, label="réel", marker='+', c='black')
    plt.plot(rang, freq_theo_min, label="théorique", c='blue')
    plt.ylabel('fréquence')
    plt.xlabel('rang')
    plt.yscale('log')
    plt.xscale('log')
    plt.legend()

    fig.tight_layout()
    plt.show()


####################################################################################################
#           Affichage Stats du traitement                                                          #
####################################################################################################



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
