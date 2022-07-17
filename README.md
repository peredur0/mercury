# mercury
***
## Ressources
* [syntax md](https://www.ionos.com/digitalguide/websites/web-development/readme-file/)
* [Gestion Warning](https://www.delftstack.com/howto/python/suppress-warnings-python/)
* [Retrait des mots non anglais](https://stackoverflow.com/questions/41290028/removing-non-english-words-from-text-using-python)

## Todo
1. Faire une schéma du flux de traitement
2. Données avant nettoyage
   1. Nombre de mail 
   2. Nombre de mots
   3. Nombre d'occurence
3. Données après nettoyage
   1. Nombre de mail
   2. Nombe de mots
   3. Nombre d'occurences
   4. Nombre de liens
   5. Distribution du nombre de mot par mail
   6. Distribution des mots (courbe de Zipf)
      1. sur l'ensemble du corpus
      2. sur les spams
      3. sur les ham
4. Traitement des données
   1. Calcul du nombre de faute
   2. Nettoyages complémentaires
      1. Retrait des mots non anglais
      2. Retrait des stop words
      3. Lemmatisation
   3. Analyse syntaxique (Standford toolkit) ?
   4. Analyse sémantique (LDA clustering) ?
   5. Création bag of word
   6. Vectorisation
5. Modèles
   1. Naive bayes
   2. SOM