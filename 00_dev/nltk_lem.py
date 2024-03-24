#! /usr/bin/env python3
# coding: utf-8

"""
Lemmatisation d'un texte et constitution du bag of word.
"""

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet

lemmatizer = WordNetLemmatizer()


def pos_tag(nltk_tag):
    assoc = {
        'J': wordnet.ADJ,
        'V': wordnet.VERB,
        'N': wordnet.NOUN,
        'R': wordnet.ADV
    }
    t = nltk_tag[0].upper()
    if t not in assoc.keys():
        return None

    return assoc[t]


def lemmatize_phrase(phrase):
    nltk_tagged = nltk.pos_tag(nltk.word_tokenize(phrase))
    wordnet_tagged = map(lambda x: (x[0], pos_tag(x[1])), nltk_tagged)
    phrase_lem = []

    for mot, tag in wordnet_tagged:
        if not tag:
            phrase_lem.append(mot)
        else:
            phrase_lem.append(lemmatizer.lemmatize(mot, tag))

    return " ".join(phrase_lem)


if __name__ == '__main__':
    nltk.download('omw-1.4')
    nltk.download('averaged_perceptron_tagger')
    test = "I am voting for that politician in this NLTK Lemmatization example sentence"

    print(lemmatizer.lemmatize(test))
    print(lemmatizer.lemmatize("voting", "v"))
    print(lemmatize_phrase(test))

    # Stop words

    # Distribution



