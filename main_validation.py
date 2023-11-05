#! /usr/bin/env python3
# coding: utf-8

"""
Validation des modèles
"""

import pickle
import re
import sys
import math
import langdetect
import nltk
import stanza
import tqdm
import main_stats
from nltk.corpus import stopwords
from traitement import nettoyage
from traitement import stats
from databases import psql_cmd
from databases.psql_db import secrets as ps_secrets
from main_nlp import lemmatise


if __name__ == '__main__':
    print("=== Validation des modèles ===")
    alg_decision_tree = pickle.load(open('./models/decision_tree_spam.sav', 'rb'))
    alg_svm = pickle.load(open('./models/svm_spam.sav', 'rb'))

    nltk.download("stopwords")
    en_stopwd = set(stopwords.words('english'))
    pipe = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma')
    pat = re.compile(r'\w+')

    with open('dev_dataset/validation/spam.csv', 'rb') as csvfile:
        csv_lines = csvfile.readlines()[1:]

    sms_data_init = []
    id_message = 0
    for line in tqdm.tqdm(csv_lines,
                          desc="-- Traitement initial des messages...",
                          leave=False,
                          file=sys.stdout,
                          ascii=True):
        infos = line.decode('utf-8', 'ignore').split(',')

        # Nettoyage initial
        corp, liens = nettoyage.clear_texte_init(infos[1])
        if not corp:
            continue

        try:
            lang = langdetect.detect(corp)
            if lang != 'en':
                continue
        except langdetect.lang_detect_exception.LangDetectException:
            continue

        new_entry = {
            'id_message': id_message,
            'categorie': infos[0],
            'message': corp}
        for key, value in liens.items():
            new_entry[key.lower()] = value

        if new_entry not in sms_data_init:
            sms_data_init.append(new_entry)
            id_message += 1
    print("-- Traitement initial des messages... OK")

    # Feature engineering
    for entry in tqdm.tqdm(sms_data_init,
                           desc='-- Traitement statistique...',
                           leave=False,
                           file=sys.stdout,
                           ascii=True):
        id_mes = entry['id_message']
        message = entry['message']
        entry.update(main_stats.stats_ponct(id_mes, message))
        entry.update(main_stats.stats_mot(id_mes, message))
        entry.update(main_stats.stats_zipf(id_mes, message))
        entry.update(main_stats.stats_hapax(id_mes, message))
    print("-- Traitement statistique... OK")

    # Vectorisation
    psql_cli = psql_cmd.connect_db(user=ps_secrets.owner,
                                   passwd=ps_secrets.owner_pw,
                                   host=ps_secrets.host,
                                   port=ps_secrets.port,
                                   dbname="mail_features_prod")
    query = "SELECT COUNT(id_message) from nlp_status WHERE success = true"
    nb_doc = psql_cmd.exec_query(psql_cli, query)[0][0]

    query = ("SELECT m.mot, a.label, m.freq_doc_all FROM tfidf_assoc as a "
             "JOIN mot_corpus AS m ON a.id_mot = m.id_mot")
    base_vector = psql_cmd.exec_query(psql_cli, query)

    psql_cli.close()

    for entry in tqdm.tqdm(sms_data_init,
                           desc='-- Vectorisation...',
                           leave=False,
                           file=sys.stdout,
                           ascii=True):
        try:
            freq_bag = stats.frequence_mot(lemmatise(entry['message'], en_stopwd, pipe, pat))
        except TypeError:
            sms_data_init.pop(sms_data_init.index(entry))
            continue

        for cellule in base_vector:
            mot, label, doc_freq = cellule
            vect_value = 0 if mot not in freq_bag else freq_bag[mot] * math.log(nb_doc/doc_freq)
            entry.update({label: vect_value})


    print('-- Vectorisation... OK')

    # Suppression des colonnes non voulues
    # Validation



