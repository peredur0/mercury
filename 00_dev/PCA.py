#! /usr/bin/env python3
# coding: utf-8

"""
Développement pour comprendre le PCA
Principal component analysis.

- source : 
    https://datascienceplus.com/principal-component-analysis-pca-with-python/
    https://www.datacamp.com/tutorial/principal-component-analysis-in-python#!

"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns


def case1():
    # Importation des données
    from sklearn.datasets import load_breast_cancer
    cancer = load_breast_cancer()
    print(cancer.keys())

    # Convert to dataframe
    df = pd.DataFrame(cancer['data'], columns=cancer['feature_names'])
    print(df.head())

    # Standardisation des données
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaler.fit(df)
    scaled_data = scaler.transform(df)

    # PCA
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2)
    pca.fit(scaled_data)
    x_pca = pca.transform(scaled_data)
    print("scaled_data.shape", scaled_data.shape)
    print("x_pca.shape", x_pca.shape)

    # Affichage des composants
    plt.figure(figsize=(8, 6))
    plt.scatter(x_pca[:, 0], x_pca[:, 1], c=cancer['target'])
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.show()


def case2():
    from sklearn.datasets import load_breast_cancer
    breats = load_breast_cancer()
    breats_data = breats.data
    print("breast_data.shape", breats_data.shape)
    breats_labels = breats.target
    print("breast_labels.shape", breats_labels.shape)


if __name__ == '__main__':
    case2()
