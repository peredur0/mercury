#! /usr/bin/env python3
# coding: utf-8

"""
Entrainement et test du modèle

Labels
    - 1 = spam
    - 2 = ham
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support as score
from sklearn.model_selection import train_test_split
from sklearn import svm
import pickle
import tqdm
from databases import psql_cmd
from databases.psql_db import secrets as ps_secrets


def get_all_data(id_message, psql_cli):
    """
    Récupération des données dans la base
    :param id_message: <int> identifiant du message
    :param psql_cli: <psycopg2.Connector> client psql
    :return: <dict>
    """
    mess_data = {'id_message': id_message}
    clause = f"id_message = {id_message}"

    mess_data.update(psql_cmd.get_data(psql_cli, 'messages', ['id_cat'], clause)[0])
    fields = ['constante', 'coefficient', 'tx_erreur']
    mess_data.update(psql_cmd.get_data(psql_cli, 'zipf', fields, clause)[0])

    fields = ['mots', 'char_min', 'char_maj', 'mot_maj', 'mot_cap']
    mess_data.update(psql_cmd.get_data(psql_cli, 'stats_mots', fields, clause)[0])

    fields = ['url', 'mail', 'nombre', 'prix']
    mess_data.update(psql_cmd.get_data(psql_cli, 'liens', fields, clause)[0])

    fields = ['h_nombre', 'ratio_unique', 'ratio_texte']
    mess_data.update(psql_cmd.get_data(psql_cli, 'hapax', fields, clause)[0])

    fields = ['point', 'exclamation', 'interrogation', 'ligne']
    mess_data.update(psql_cmd.get_data(psql_cli, 'stat_ponct', fields, clause)[0])

    fields = [row['label'] for row in psql_cmd.get_data(psql_cli, 'tfidf_assoc', ['label'])]
    mess_data.update(psql_cmd.get_data(psql_cli, 'tfidf_vector', fields, clause)[0])

    return mess_data


if __name__ == '__main__':
    psql_db = "mail_features_prod"
    psql_cli = psql_cmd.connect_db(dbname=psql_db,
                                   user=ps_secrets.owner,
                                   passwd=ps_secrets.owner,
                                   host=ps_secrets.host,
                                   port=ps_secrets.port)

    print("=== Phase 3: Création du modèle ===")

    full_data = []
    for entry in tqdm.tqdm(psql_cmd.get_data(psql_cli, 'nlp_status',
                                             ['id_message'], "success = true"),
                           desc='Récupération des données',
                           leave=False,
                           ascii=True):
        full_data.append(get_all_data(entry.get('id_message'), psql_cli))

    mail_df = pd.DataFrame(full_data)
    print('Récupération des données... OK')

    mail_cat = mail_df['id_cat']
    mail_df.drop(['id_cat'], axis=1, inplace=True)
    x_train, x_test, y_train, y_test = train_test_split(mail_df, mail_cat, test_size=0.25)

    # Mono decision tree
    alg_decision_tree = RandomForestClassifier(n_estimators=1, max_depth=60, n_jobs=-1)
    model = alg_decision_tree.fit(x_train, y_train)
    predictions = model.predict(x_test)
    precision, recall, fscore, support = score(y_test, predictions, pos_label=1, average='binary')

    print(f"--- Random Tree forest ---\n"
          f"Precision: {round(precision, 3)} // Recall: {round(recall, 3)} "
          f"// Accurancy: {round((predictions==y_test).sum()/len(predictions), 3)}")

    # SVM
    alg_svm = svm.SVC(kernel='linear')
    alg_svm.fit(x_train, y_train)
    predictions = alg_svm.predict(x_test)
    precision, recall, _, _ = score(y_test, predictions, pos_label=1, average='binary')
    accuracy = (predictions == y_test).sum()/len(predictions)
    print(f"--- Support Vector machine ---\n"
          f"Precision: {round(precision, 3)} // Recall: {round(recall, 3)} "
          f"// Accurancy: {round(accuracy, 3)}")

    # Sauvegarder les modèles
    pickle.dump(alg_decision_tree, open('./models/decision_tree_spam.sav', 'wb'))
    pickle.dump(alg_svm, open('./models/svm_spam.sav', 'wb'))
    print("Modèles sauvegardé")
