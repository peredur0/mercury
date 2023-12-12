#! /usr/bin/env python3
# coding: utf-8

"""
Validation des modèles
"""

import pickle
import re
import sys
import math
import csv
import langdetect
import nltk
import stanza
import torch
import tqdm
import main_stats
import pandas as pd
from nltk.corpus import stopwords
from traitement import nettoyage
from traitement import stats
from traitement import ml
from databases import psql_cmd
from main_nlp import lemmatise
from databases.psql_db import secrets as ps_secrets
from sklearn.metrics import precision_recall_fscore_support as score


if __name__ == '__main__':
    print("=== Validation des modèles ===")
    alg_decision_tree = pickle.load(open('./models/decision_tree_spam.sav', 'rb'))
    alg_svm = pickle.load(open('./models/svm_spam.sav', 'rb'))
    df_columns = pickle.load(open('./models/df_columns.sav', 'rb'))

    nltk.download("stopwords")
    en_stopwd = set(stopwords.words('english'))
    pipe = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma')
    pat = re.compile(r'\w+')

    file = 'dev_dataset/validation/spam_ham_dataset.csv'
    # with open(file, 'rb') as csvfile:
    #     csv_lines = csvfile.readlines()[1:]
    reader = csv.DictReader(open(file))

    sms_data_init = []
    id_message = 0
    for line in tqdm.tqdm(reader,
                          desc="-- Traitement initial des messages...",
                          leave=False,
                          file=sys.stdout,
                          ascii=True):
        # infos = line.decode('utf-8', 'ignore').split(',')

        # Adapter selon le dataset de validation
        message = '\n'.join(line['text'].splitlines()[1:])
        categorie = 1 if line['label'] == 'spam' else 2

        # Nettoyage initial
        corp, liens = nettoyage.clear_texte_init(message)
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
            'categorie': categorie,
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
        except torch.cuda.OutOfMemoryError:
            sms_data_init.pop(sms_data_init.index(entry))
            continue

        for cellule in base_vector:
            mot, label, doc_freq = cellule
            vect_value = 0 if mot not in freq_bag else freq_bag[mot] * math.log(nb_doc/doc_freq)
            entry.update({label: vect_value})

    print('-- Vectorisation... OK')

    print('== Validation')
    validation_df = pd.DataFrame(sms_data_init)
    validation_cat = validation_df['categorie']
    validation_df = validation_df[df_columns]
    validation_df.fillna(0, inplace=True)
    ml.std_normalise(validation_df)

    predictions = alg_decision_tree.predict(validation_df)
    precision, recall, fscore, support = score(validation_cat, predictions, pos_label=1,
                                               average='binary')

    print(f"--- Random Tree forest ---\n"
          f"Precision: {round(precision, 3)} // Recall: {round(recall, 3)} "
          f"// Accurancy: {round((predictions == validation_cat).sum() / len(predictions), 3)}")

    predictions = alg_svm.predict(validation_df)
    precision, recall, _, _ = score(validation_cat, predictions, pos_label=1, average='binary')
    accuracy = (predictions == validation_cat).sum() / len(predictions)
    print(f"--- Support Vector machine ---\n"
          f"Precision: {round(precision, 3)} // Recall: {round(recall, 3)} "
          f"// Accurancy: {round(accuracy, 3)}")



