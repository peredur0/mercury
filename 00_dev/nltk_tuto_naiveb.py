#! /usr/bin/env python3
# coding: utf-8

"""
Fichier de test pour le sentiment analysis

Processus :
- Chargement des données
- Création des sac de mots avec la catégortie
- Extraction des caractérisques principales
    > Focus sur les 2000 mots les plus présent dans le dataset
    > verification de tous les documents avec les mots importants
    > par documents ({MOTS IMPORTANTS: True|False}, catégorie)
- Séparation des set, en train et test
- Entrainement du modèle
- Test du modèle

"""

# Importation du dataset
import nltk
from nltk.corpus import movie_reviews
import random

nltk.download('movie_reviews')
documents = [(list(movie_reviews.words(fileid)), category)
             for category in movie_reviews.categories()
             for fileid in movie_reviews.fileids(category)]

random.shuffle(documents)
# document : ([BAG OF WORD], CATEGORIE)

# extracteur de caractéristiques
# permettre au classifier de se focaliser sur les mots les plus fréquents dans le corpus

all_words = nltk.FreqDist(w.lower() for w in movie_reviews.words())
word_features = list(all_words)[:3000]


def document_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features['contains({})'.format(word)] = (word in document_words)
    return features


# entrainment Naive Bayes moteur
featureset = [(document_features(d), c) for (d, c) in documents]
train_set, test_set = featureset[100:], featureset[:100]
classifier = nltk.NaiveBayesClassifier.train(train_set)

# Test du moteur
print("Précision :", nltk.classify.accuracy(classifier, test_set))

# Montrer les features les plus pertinentes
classifier.show_most_informative_features(5)

