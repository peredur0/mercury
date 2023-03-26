#! /usr/bin/env python3
# coding: utf-8

"""
    Module pour le test du modèle Naives Bayes
"""
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, f1_score

import matplotlib.pyplot as plt

if __name__ == '__main__':
    X, y = load_iris(return_X_y=True)

    # data visualisation
    plt.scatter(X[:, 0], X[:, 1], c=y)
    plt.show()

    # Model creation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=0)
    model = GaussianNB()
    model.fit(X_train, y_train)

    # Model evaluation
    y_pred = model.predict(X_test)
    precision = accuracy_score(y_pred, y_test)
    f1 = f1_score(y_pred, y_test, average="weighted")

    print("Précision:", precision)
    print("Score F1:", f1)

    labels = [0, 1, 2]
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot()
    plt.show()
