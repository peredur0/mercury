#! /usr/bin/env python3
# coding: utf-8

"""
    Module des traitements pour le ML
"""

from sklearn import preprocessing


def std_normalise(data):
    """
    Normaliseur standard d'un dataframe
    :param data: pandas.DataFrame
    :return: <None>
    """
    for col in data.columns:
        x = data[[col]].values.astype(float)
        std_normalizer = preprocessing.StandardScaler()
        data[col] = std_normalizer.fit_transform(x)
