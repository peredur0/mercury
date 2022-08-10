# mercury
***
## Ressources
* [syntax md](https://www.ionos.com/digitalguide/websites/web-development/readme-file/)
* [Gestion Warning](https://www.delftstack.com/howto/python/suppress-warnings-python/)
* [Retrait des mots non anglais](https://stackoverflow.com/questions/41290028/removing-non-english-words-from-text-using-python)

## Todo
1. Faire une schéma du flux de traitement
2. Données avant create_document > ok
   1. Nombre de mail > ok
   2. Nombre de mots > ok
   3. Nombre de mots uniques > ok  
3. Données après create_document > ok
   1. Nombre de mail > ok
   2. Nombe de mots > ok
   3. Nombre de mots uniques > ok
   4. Nombre de liens > ok
4. Analyse Statistiques
   1. Distribution de zipf > ok
      1. Triage des mots > ok
      2. Représentation graphique de test (corpus brown) > ok
      3. Détermination constante et coefficient > ok
      4. Détermination du cout minimum > ok
   2. Caclul du ratio d'hapax > ok
      1. Comptage du nombre d'hapax > ok
      2. Calcul du ratio texte > ok
      3. Calcul du ratio mots > ok
5. Analyse langage (NLP)
   1. Calcul du nombre de fautes
   2. Standford NLP
      1. POS tagger
      2. Lemmatisation
      3. Name Entity Recognizier
   3. NLTK
      1. stopwprds
      2. non english words
6. Vectorisation 
   1. gensim (Word2Vec en python)
7. Features engineering 
   1. Sentiment analysis
   2. Topic detection (LDA clustering)

6. Aanalyse Corpus (corpus - spam - ham)
   1. Courbe de zipf - étude distribution des mots
   2. Dist, avg, med : nombre de mots
   3. Dist, avg, med : nombre de mots uniques
   4. Dist, avg, med : liens
   5. Dist, avg, med : fautes
   6. Dist, avg, med : Nombre de nom propre

afficher des courbes de la recherche de minimum de cout pour justifier les choix. > ok

7. Traitement des données - analyse
   1. Calcul du nombre de faute
   2. Nettoyages complémentaires
      1. Retrait des mots non anglais
      2. Retrait des stop words
      3. Lemmatisation
   3. Analyse syntaxique (Standford toolkit) ?
   4. Analyse sémantique (LDA clustering) ?
   5. Création bag of word
   6. Vectorisation
8. Modèles
   1. Naive bayes
   2. SOM

## Difficultées
1. Réaliser la distribution de zipf.
   * Trouver la manière de calculer la coubre théorique. 
   Réussi en travaillant sur le corpus de Brown (NLTK) qui contient 1161192 mots d'ouvrage en anglais américain contemporain. 
   Pour déterminer la constante du texte, je fais la moyenne des occurences fois le rang puissance S. la valeur S me sert
   de variable d'ajustement afin d'avoir le coup (écart absolu entre réel et théorique) le plus réduit. 
   # help : https://iq.opengenus.org/zipfs-law/
   # help : https://www.youtube.com/watch?v=WYO8Rc4JB_Y