#! /usr/bin/env python3
# coding: utf-8

"""
Phase 2: Exploitation (pour chaque document, pour tous les SPAM, HAM et pour tout les documents)
  Données statistiques:
    - Distribution de ZIPF
        Le mot le plus fréquent est 2 fois plus présent que le 2, 3 fois plus que le 3e etc
    - Distribution selon la taille des mots
        > Pour les textes aléatoires les mots les plus courts sont plus fréquent
    - Proportion d'HAPAX (la proportion de mot n'ayant qu'une seule occurence doit être vers 50%)

    ==> Résultat avec ou sans analyse syntaxique (Standford ou nltk)
    ==> Système de scoring ELK pour les mails, sqlite pour les catégories

  Données sémantiques
    - Extraction des thèmes
"""
import re
import sys
import tqdm

from traitement import stats
from databases import elastic_cmd, psql_cmd
from databases.elastic import secrets as es_secrets
from databases.psql_db import secrets as ps_secrets


def recup_mails(es_index):
    """
    Récuperation des mails dans la base psql
    :param es_index: <str> nom de l'index ES où recupérer les données
    :return: <dict> Dictionnaire avec les données des mails
    """
    es_cli = elastic_cmd.es_connect(es_secrets.serveur, (es_secrets.apiid, es_secrets.apikey),
                                    es_secrets.ca_cert)
    data = {}
    for cat in ['spam', 'ham']:
        print("-- Récupération des {}...".format(cat), end=' ')
        data[cat] = {entry.get('_source').get('hash'): entry.get('_source').get('message')
                     for entry in elastic_cmd.es_get_all(es_cli, es_index, sort={'hash': 'asc'},
                                                         query={'match': {'categorie': cat}})}
        print('OK')
    return data


def stats_ponct(id_text, texte):
    """
    Genere les stats pour la table de ponctuation
        points, virgule, espaces, lignes
    :param id_text: <int> identifiant interne du texte
    :param texte: <str> texte a analyser
    :return: <dict> données e stocker en base
    """
    return {
        "id_message": id_text,
        "point": texte.count('.'),
        "virgule": texte.count(','),
        "exclamation": texte.count('!'),
        "interrogation": texte.count('?'),
        "tabulation": texte.count('\t'),
        "espace": texte.count(' '),
        "ligne": texte.count('\n') + 1,
        "ligne_vide": len(re.findall(r'^\s*$', texte, re.MULTILINE))
    }


def stats_mot(id_text, texte):
    """
    Genere les stats pour la table des mots
        mots, char non vide
    :param id_text: <int> identifiant interne du texte
    :param texte: <str> texte a analyser
    :return: <dict> avec les données
    """
    tokens = re.findall(r'\w+', texte, re.MULTILINE)
    # Meilleure méthode que pour le comptage des mots fait avec un simple split dans la phase 1.
    return {
        'id_message': id_text,
        'char_min': len(re.findall(r'[a-z]', texte, re.MULTILINE)),
        'char_maj': len(re.findall(r'[A-Z]', texte, re.MULTILINE)),
        'mots': len(tokens),
        'mots_uniques': len(set(tokens)),
        'mot_maj': sum(mot.isupper() for mot in tokens),
        'mot_cap': sum(bool(re.match(r'[A-Z][a-z]+', mot)) for mot in tokens)
    }


def stats_zipf(id_text, texte):
    """
    Genere les informations de la distribution de zipf
    :param id_text: <int> identifiant interne du texte
    :param texte: <str> message
    :return: <dict> avec les données
    """
    tokens = re.findall(r'\w+', texte, re.MULTILINE)
    data = stats.zipf_process(tokens)
    data['id_message'] = id_text
    data['constante'] = data.pop('const_moy')
    data['coefficient'] = data.pop('coef_min')
    data['tx_erreur'] = data.pop('cout_min')

    return data


def stats_hapax(id_text, texte):
    """
    Genere les informations de la distribution de zipf
    :param id_text: <int> identifiant interne du texte
    :param texte: <str> message
    :return: <dict> avec les données
    """
    tokens = re.findall(r'\w+', texte, re.MULTILINE)
    data = stats.hapax(tokens)
    data['id_message'] = id_text
    data['h_nombre'] = data.pop('nombres')
    data['ratio_unique'] = data.pop('ratio_mots_uniques')

    return data


def stats_pipe_message(hash_message, message, psql_cli):
    """
    Pipeline des statistiques
    :param hash_message: <str> identifiant unique du message
    :param message: <str> message à analyser
    :param psql_cli: <psycopg2.extension.connection> client PSQL
    :return: <None>
    """
    resp = psql_cmd.get_data(psql_cli, 'messages', ['id_message'], f"hash LIKE '{hash_message}'")
    if not resp:
        print(f"No id_message found for {hash_message}", file=sys.stderr)
        return
    id_mess = resp[0].get('id_message')

    for table, stat_func in {'stat_ponct': stats_ponct,
                             'stats_mots': stats_mot,
                             'zipf': stats_zipf,
                             'hapax': stats_hapax}.items():
        resp = psql_cmd.get_data(psql_cli, table, ['id_message'], f"id_message={id_mess}")
        if resp:
            continue
        psql_cmd.insert_data(psql_cli, table, stat_func(id_mess, message))


def stats_pipe_globale(data):
    """
    Pipeline de recupération des stats globales
    :param data: <dict> dictionnaire avec les messages ham et spam
    :return: <None>
    """
    # Données globales
    ls_ham = [mess for mess in data['ham'].values()]
    ls_spam = [mess for mess in data['spam'].values()]
    tokens = []
    for mess in ls_ham + ls_spam:
        tokens += re.findall(r'\w+', mess, re.MULTILINE)
    data = stats.zipf_process(tokens, True)
    print("Données Zipf ham+spam:", data)
    data = stats.hapax(tokens)
    print("Données Hapax ham+spam:", data)

    tokens = []
    for mess in ls_ham:
        tokens += re.findall(r'\w+', mess, re.MULTILINE)
    data = stats.zipf_process(tokens, True)
    print("Données Zipf ham:", data)
    data = stats.hapax(tokens)
    print("Données Hapax ham:", data)

    tokens = []
    for mess in ls_spam:
        tokens += re.findall(r'\w+', mess, re.MULTILINE)
    data = stats.zipf_process(tokens, True)
    print("Données Zipf spam:", data)
    data = stats.hapax(tokens)
    print("Données Hapax spam:", data)


if __name__ == '__main__':
    print("=== Phase 2 : Stats Exploitation ===")

    p_data = recup_mails('import_prod')
    psql_cli = psql_cmd.connect_db('mail_features_prod', ps_secrets.owner, ps_secrets.owner,
                                   ps_secrets.host, ps_secrets.port)

    print('-- Récupération des statistiques par message')
    for key, value in tqdm.tqdm(p_data['spam'].items(),
                                desc="Stats Spam...",
                                leave=False,
                                file=sys.stdout):
        stats_pipe_message(key, value, psql_cli)
    print("Stats Spam... OK")

    for key, value in tqdm.tqdm(p_data['ham'].items(),
                                desc="Stats Ham...",
                                leave=False,
                                file=sys.stdout):
        stats_pipe_message(key, value, psql_cli)
    print("Stats Ham... OK")

    print('-- Récupérations des statistiques globales')
    stats_pipe_globale(p_data)

    psql_cli.close()


