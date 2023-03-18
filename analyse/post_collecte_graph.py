#! /usr/bin/env python3
# coding: utf-8

"""
    Récupère les données statistiques de la collecte et les met en forme
"""
import sys
from databases import sqlite_cmd
import matplotlib.pyplot as plt
import numpy as np


def display_bar_etapes(data, subp):
    """
    Affiche les donnees des etapes sous forme de bar.
    :param data: <param> dict données des requetes SQL.
    :param titre: <str> titre du graph
    :return: subplot
    """
    etapes = [entry[0] for entry in data]
    stat_data = {
        'global': [entry[1] for entry in data],
        'ham': [entry[2] for entry in data],
        'spam': [entry[3] for entry in data]
    }

    x = np.arange(len(etapes))
    width = 0.25
    multiplier = 0

    for scope, value in stat_data.items():
        offset = width * multiplier
        rects = subp.bar(x + offset, value, width, label=scope)
        subp.bar_label(rects, padding=3)
        multiplier += 1

    subp.set_xticks(x + width, etapes)
    # subp.legend()


if __name__ == '__main__':
    sqlite_db = '../databases/sqlite_db/stats_dev.db'
    sql_client = sqlite_cmd.sl_connect(sqlite_db)

    fig = plt.figure("Stats en cours de récolte", figsize=(17, 5))
    fig.subplots_adjust(wspace=0.4)
    position = 1

    for key, titre in [('mails', 'Documents conservés'), ('mots', 'Nombre de mots'),
                       ('mots_uniques', 'Nombre de mots uniques')]:
        req = f"select g.etape, g.{key}, h.{key}, s.{key} from globales as g " \
              f"join ham as h on g.etape like h.etape " \
              f"join spam as s on g.etape like s.etape"
        result = sqlite_cmd.sl_select(sql_client, req)
        ax = plt.subplot(1, 3, position, title=titre)
        ax.set_ylabel(key)
        display_bar_etapes(result, ax)
        position += 1

    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, ncols=3, loc='upper center')

    sql_client.close()
    plt.show()
    sys.exit(0)
