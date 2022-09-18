#! /usr/bin/env python3
# coding: utf-8

"""
Travaille de recherche sur la distribution de zipf.

Recherche de la méthode pour trouver les paramètres avec un cout minimum entre la théorie et la pratique

Corpus utilisés : ntlk brown, stopwords
utilisation d'un grand dataset préformaté correct avant de l'employer sur mon nettoyage de mail


Après analyse j'obtiens de meilleurs résultats sans retirer les stopswords anglais
et en utilisant une constante moyenne plutôt que médiane
"""
import re
import nltk
import matplotlib.pyplot as plt
import numpy as np
from nltk.corpus import brown, stopwords
from traitement.stats import frequence_mot, classement_zipf, zipf_freq_theorique, cout


if __name__ == '__main__':
    nltk.download("brown")
    nltk.download("stopwords")

    # Récolte
    datas_brown = brown.words()
    stopw = set(stopwords.words('english'))

    # Nettoyage + frequence
    print("-- Récupération du dataset...", end=' ')
    brown_freq = frequence_mot([w.lower() for w in datas_brown if re.match(r'\w+', w)])
    brown_stop_freq = frequence_mot([w.lower() for w in datas_brown if (re.match(r'\w+', w) and w not in stopw)])
    print("ok")

    print(f"Nombre de mots dans brown:\t"
          f"mots: {len(brown_freq.keys())}\t"
          f"occurences: {sum(list(brown_freq.values()))}")
    print(f"Nombre de mots dans brown stop:\t"
          f"mots: {len(brown_stop_freq.keys())}\t"
          f"occurences: {sum(list(brown_stop_freq.values()))}")

    # Classement zipf
    print("-- Classement selon fréquence...", end=' ')
    zipf_brown = classement_zipf(brown_freq)
    zipf_brown_s = classement_zipf(brown_stop_freq)

    zb_rang, zb_freq = zip(*[(e['rang'], e['frequence']) for e in zipf_brown])
    zbs_rang, zbs_freq = zip(*[(e['rang'], e['frequence']) for e in zipf_brown_s])
    print("ok")

    # Détermination des constantes
    print("-- Recherche des constantes...", end=' ')
    zb_const = [e['rang'] * e['frequence'] for e in zipf_brown]
    zb_const_moyen = np.mean(zb_const)
    zb_const_median = np.median(zb_const)

    zbs_const = [e['rang'] * e['frequence'] for e in zipf_brown_s]
    zbs_const_moyen = np.mean(zbs_const)
    zbs_const_median = np.median(zbs_const)
    print("ok")

    # Recherche du coefficiant
    print("-- Recherche du coefficiant...", end=' ')
    ls_coef = list(np.arange(0.86, 1.3, 0.01))
    zbmo_th = {coef: [zipf_freq_theorique(zb_const_moyen, r, coef) for r in zb_rang] for coef in ls_coef}
    zbme_th = {coef: [zipf_freq_theorique(zb_const_median, r, coef) for r in zb_rang] for coef in ls_coef}
    zbmoth_cmoy = [cout(zb_freq, zbmo_th[coef], 'absolue') for coef in ls_coef]
    zbmeth_cmoy = [cout(zb_freq, zbme_th[coef], 'absolue') for coef in ls_coef]

    zbsmo_th = {coef: [zipf_freq_theorique(zbs_const_moyen, r, coef) for r in zbs_rang] for coef in ls_coef}
    zbsme_th = {coef: [zipf_freq_theorique(zbs_const_median, r, coef) for r in zbs_rang] for coef in ls_coef}
    zbsmoth_cmoy = [cout(zbs_freq, zbsmo_th[coef], 'absolue') for coef in ls_coef]
    zbsmeth_cmoy = [cout(zbs_freq, zbsme_th[coef], 'absolue') for coef in ls_coef]
    print("ok")

    print(f"cout min brown moyenne: {min(zbmoth_cmoy)}, median: {min(zbmeth_cmoy)}")
    print(f"cout min brown (- stopwords) moyenne: {min(zbsmoth_cmoy)}, median: {min(zbsmeth_cmoy)}")
    zbmot_coef_cmin = list(zbmo_th.keys())[zbmoth_cmoy.index(min(zbmoth_cmoy))]
    zbmet_coef_cmin = list(zbme_th.keys())[zbmeth_cmoy.index(min(zbmeth_cmoy))]

    zbsmot_coef_cmin = list(zbsmo_th.keys())[zbsmoth_cmoy.index(min(zbsmoth_cmoy))]
    zbsmet_coef_cmin = list(zbsme_th.keys())[zbsmeth_cmoy.index(min(zbsmeth_cmoy))]

    print(f"Coefficient min brown moyenne: {zbmot_coef_cmin}, median: {zbmet_coef_cmin}")
    print(f"Coefficient min brown (- stopwords) moyenne: {zbsmot_coef_cmin}, median: {zbsmet_coef_cmin}")

    # Process graphique
    ligne = 2
    colonne = 4
    pos = 1
    plt.figure("Analyse des données pour zipf", figsize=(10, 10))
    # == Brown
    # Zipf brut
    plt.subplot(ligne, colonne, pos, title="Distribution brown")
    plt.scatter(zb_rang, zb_freq, label="réel", marker='+', c="black")
    plt.ylabel('fréquence')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    # Estimation de la constante
    pos += 1
    plt.subplot(ligne, colonne, pos, title="Constante estimée brown")
    plt.plot(zb_rang, zb_const, label='rang x frequence', c='black')
    plt.plot(zb_rang, [zb_const_moyen] * (len(zb_rang)), label="moyenne", c='blue')
    plt.plot(zb_rang, [zb_const_median] * (len(zb_rang)), label="median", c='green')
    plt.ylabel('constante')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    # cout
    pos += 1
    plt.subplot(ligne, colonne, pos, title="Moyenne cout brown")
    plt.plot(ls_coef, zbmoth_cmoy, label="constante moyenne, absolue", c='blue')
    plt.plot(ls_coef, zbmeth_cmoy, label="constante mediane, absolue", c='green')
    plt.ylabel('cout')
    plt.legend()
    # estimation freq
    pos += 1
    plt.subplot(ligne, colonne, pos, title="Distribution brown avec estimation")
    plt.scatter(zb_rang, zb_freq, label="réel", marker='+', c="black")
    plt.plot(zb_rang, zbmo_th[zbmot_coef_cmin], label=f'théo avg, coef {zbmot_coef_cmin:.2f}', c="blue")
    plt.plot(zb_rang, zbme_th[zbmet_coef_cmin], label=f'théo med, coef {zbmet_coef_cmin:.2f}', c="green")
    plt.ylabel('fréquence')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()

    # == Brown sans stopwords
    # zipf brut
    pos += 1
    plt.subplot(ligne, colonne, pos, title="Distribution brown (-stopwords)")
    plt.scatter(zbs_rang, zbs_freq, label="réel", marker='+', c='black')
    plt.xlabel('rang')
    plt.ylabel('fréquence')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    # Estimation de la constante
    pos += 1
    plt.subplot(ligne, colonne, pos, title="Constante estimée brown (-stopwords)")
    plt.plot(zb_rang, zb_const, label='rang x frequence', c='black')
    plt.plot(zb_rang, [zbs_const_moyen] * (len(zb_rang)), label="moyenne", c='blue')
    plt.plot(zb_rang, [zbs_const_median] * (len(zb_rang)), label="median", c='green')
    plt.xlabel('rang')
    plt.ylabel('constante')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    # cout
    pos += 1
    plt.subplot(ligne, colonne, pos, title="Moyenne cout brown (-stopwords)")
    plt.plot(ls_coef, zbsmoth_cmoy, label="constante moyenne", c='blue')
    plt.plot(ls_coef, zbsmeth_cmoy, label="constante mediane", c='green')
    plt.ylabel('cout')
    plt.xlabel('coefficient')
    plt.legend()
    # estimation freq
    pos += 1
    plt.subplot(ligne, colonne, pos, title="Distribution brown (-stopwords) avec estimation")
    plt.scatter(zbs_rang, zbs_freq, label="réel", marker='+', c='black')
    plt.plot(zbs_rang, zbsmo_th[zbsmot_coef_cmin], label=f'théo avg, coef {zbsmot_coef_cmin:.2f}', c="blue")
    plt.plot(zbs_rang, zbsme_th[zbsmet_coef_cmin], label=f'théo med, coef {zbsmet_coef_cmin:.2f}', c="green")
    plt.xlabel('rang')
    plt.ylabel('fréquence')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()

    plt.show()

    exit(0)
