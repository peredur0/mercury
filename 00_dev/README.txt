Organisation du process pour l'analyse des mails :

1. Récupération des mails brut :
    - fichier CSV - enron
    - fichiers mail trié - spamassassin

2. Importation dans python (shj_import.py)
    - Chargement des mails - email
    - convertion en utf8 - chardet
    - extraction des métadonnées (sujet, from)
    - extraction du corps du texte
        > 3.

3. Nettoyage primaire (shj_clear.py)
    - retrait des balises HTML - BeautifulSoup
    - retrait balises <> - re
    - texte en lowercase
    - retrait des réponses - re
    - substitution des lien, nombres + prix
    - retrait ponctuation superflue - re
    - retrait char non ascii

4. Mise en base (shj_elastic.py)
    - création d'un document
        > hash - hashlin
        > chemin - sys
        > categorie
        > sujet
        > expediteur
        > nombres_mots
        > subsitutions : {URL, TEL, MAIL, PRIX, NOMBRE}
        > message
    - mise en base du document - elasticsearch

5. Hyperparamètres (???.py)
    - Récupération des corps et hash
    - calcul du nombre de fautes - language-tool-python
    - retrait des stopwords EN
    - création du bag of word nltk
    - score bag of word - ntlk.NaiveBayesClassifier

6. Entrainement du modèle
    -

7. Utilisation sur enron mail
    -