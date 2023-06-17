#! /usr/bin/env python3
# coding: utf-8

"""
Module de traitement du texte

NLP :
    - Process :
        1. tokenisation
        2. Pos tagging
        3. lemmas / name entity
        4. - stopwords & non english words

Outils:
    - StandfordNLP
        * tokenisation
        * POS tagging
        * lemmas

    - nltk
        * stopwords
        * english words

Features annexes:
    - Comptage du nombre et type de faute
"""

####################################################################################################
#             NLP processing                                                                       #
####################################################################################################

import stanza

if __name__ == '__main__':
    nlp = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma')
    doc = nlp("Barack Obama was born in Hawaii. I'm living in France.\nYou are near me")
    print(*[f'word: {word.text+" "}\tlemma: {word.lemma}' for sent in doc.sentences for word in sent.words], sep='\n')

