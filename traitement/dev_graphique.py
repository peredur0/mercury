#! /usr/bin/env python3
# coding: utf-8

"""
Développement des fonction graphiques
"""

import matplotlib.pyplot as plt


if __name__ == '__main__':
    x = list(range(1, 10))
    y = [c ** 2 for c in x]

    plt.figure()
    plt.plot(x, y, label='carré', lw=1, c='red')
    plt.plot(x, [c**3 for c in x], label="cube")
    plt.title('figure 1')
    plt.xlabel('axe x')
    plt.ylabel('axe y')
    plt.legend()
    plt.show()
    # plt.savefig("save_fig1.png")

    # plusieurs graph dans une figure
    plt.figure()
    plt.subplot(2, 1, 1)
    exit(0)
