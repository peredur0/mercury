#! /usr/bin/env python3
# coding: utf-8

"""
Récupération de tous les mails par petit lots
"""

from elasticsearch import Elasticsearch


def search_in_spam():
    SAMPLE_SIZE = 100
    index = 'mails_1'
    server = "https://localhost:9200"
    creds = ("elastic", "elastic123")
    es_client = Elasticsearch(server, basic_auth=creds, ca_certs="./data/ca.crt")

    query = {
        "match": {
            "categorie": "spam"
        }
    }

    sortie = es_client.search(index=index, size=SAMPLE_SIZE, query=query, source=False, fields=['nombres_mots', 'hash'])
    for hit in sortie['hits']['hits']:
        print(hit['fields']['hash'][0], ':', hit['fields']['nombres_mots'][0])


def search_all():
    MAX_SIZE = 10000
    SORT = "hash.keyword"
    index_mail = 'mails_1'
    server = "https://localhost:9200"
    creds = ("elastic", "elastic123")

    es_client = Elasticsearch(server, basic_auth=creds, ca_certs="./data/ca.crt")

    # récupérer le nombre de documents
    query_all = {
        "match_all": {}
    }

    # Récupération du nombre total de documents
    rep = es_client.count(index=index_mail, query=query_all)
    nb_doc = rep['count']
    print("Nombre de documents :", nb_doc)

    count = 0
    sortie = es_client.search(index=index_mail, size=MAX_SIZE, sort={SORT: "asc"}, query=query_all)
    signet = sortie['hits']['hits'][-1]['sort']
    for hit in sortie['hits']['hits']:
        # Fonction à executer sur les résultat
        count += 1

    sortie = es_client.search(index=index_mail,
                              size=MAX_SIZE,
                              sort={SORT: 'asc'},
                              query=query_all,
                              search_after=signet)

    signet = sortie['hits']['hits'][-1]['sort']
    for hit in sortie['hits']['hits']:
        # Fonction à executer sur les résultat
        count += 1

    while count < nb_doc:
        sortie = es_client.search(index=index_mail,
                                  size=MAX_SIZE,
                                  sort={SORT: 'asc'},
                                  query=query_all,
                                  search_after=signet)
        try:
            signet = sortie['hits']['hits'][-1]['sort']
        except IndexError:
            print("WARNING", sortie)
            print("WARNING", signet)
            break

        for hit in sortie['hits']['hits']:
            # Fonction à executer sur les résultat
            count += 1

        print("Count :", count)

    print("FINAL : ", count)


if __name__ == '__main__':
    # search_all()
    search_in_spam()
