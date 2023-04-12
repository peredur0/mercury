#! /usr/bin/env python3
# coding: utf-8

"""
    Module pour le test du modèle Naives Bayes
"""
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, f1_score, \
    recall_score

import matplotlib.pyplot as plt

if __name__ == '__main__':
    X, y = load_iris(return_X_y=True)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=0)
    model = GaussianNB()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    precision = accuracy_score(y_pred, y_test)
    recall = recall_score(y_test, y_pred, average="weighted")
    f1 = f1_score(y_pred, y_test, average="weighted")

    print("Précision:", precision)
    print("Rappel:", recall)
    print("Score F1:", f1)

    plt.figure('Données du modèle', figsize=(14, 5))
    plt.subplot(1, 3, 1, title='Données du train set')
    plt.scatter(X_train[:, 0], X_train[:, 1], c=y_train)
    plt.xlabel('Sépale long.')
    plt.ylabel('Sépale larg.')
    plt.subplot(1, 3, 2, title='Données du test set')
    plt.scatter(X_test[:, 0], X_test[:, 1], c=y_test)
    plt.xlabel('Sépale long.')
    plt.subplot(1, 3, 3, title='Données test après évaluation')
    plt.scatter(X_test[:, 0], X_test[:, 1], c=y_pred)
    plt.xlabel('Sépale long.')
    plt.show()

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1, 2])
    disp.plot()
    plt.show()

    plt.figure('Distribution des données Iris', figsize=(14, 5))
    plt.subplot(1, 2, 1, title='Longueur sépale')
    plt.hist(X[:, 0], bins=15)
    plt.subplot(1, 2, 2, title='Largeur sépale')
    plt.hist(X[:, 1], bins=15)
    plt.show()
