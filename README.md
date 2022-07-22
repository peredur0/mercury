# mercury
***
## Ressources
* [syntax md](https://www.ionos.com/digitalguide/websites/web-development/readme-file/)
* [Gestion Warning](https://www.delftstack.com/howto/python/suppress-warnings-python/)
* [Retrait des mots non anglais](https://stackoverflow.com/questions/41290028/removing-non-english-words-from-text-using-python)

## Todo
1. Faire une schéma du flux de traitement
2. Données avant nettoyage > ok
   1. Nombre de mail 
   2. Nombre de mots 
   3. Nombre de mots uniques  
3. Données après nettoyage > ok
   1. Nombre de mail
   2. Nombe de mots
   3. Nombre de mots uniques
   4. Nombre de liens
4. Exploitation
   1. Calcul du nombre de fautes
   2. Analyse syntaxique Standford NLP
      1. POS tagger
      2. Lemmatisation
      3. Name Entity Recognizier
   3. Analyse syntaxique NLTK ?
   4. Analyse sémentique LDA
5. Analyse (corpus - spam - ham)
   1. Courbe de zipf - étude distribution des mots
   2. Dist, avg, med : nombre de mots
   3. Dist, avg, med : nombre de mots uniques
   4. Dist, avg, med : liens
   5. Dist, avg, med : fautes
   6. Dist, avg, med : Nombre de nom propre
   7. 

6. Traitement des données - analyse
   1. Calcul du nombre de faute
   2. Nettoyages complémentaires
      1. Retrait des mots non anglais
      2. Retrait des stop words
      3. Lemmatisation
   3. Analyse syntaxique (Standford toolkit) ?
   4. Analyse sémantique (LDA clustering) ?
   5. Création bag of word
   6. Vectorisation
7. Modèles
   1. Naive bayes
   2. SOM