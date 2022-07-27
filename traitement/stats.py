#! /usr/bin/env python3
# coding: utf-8

"""
    Module d'exploitation:
        - traitement NLP
            - nltk - tokenisation, POS tagging,  lemmatisation, stopwords
            - Standford - tokenisation, POS tagging, lemmatisation, noms propres
            - calcul de la distribution des tag.

        - travail sur la fréquence des mots
            * récupération de la fréquence pour les mots d'un texte
            * loi de Zipf
                - calculer le nombre d'occurences théorique par mot selon son rang
                - calculer l'écart entre le nombre d'occurence théorique et la réalité du texte
                    (sur tout le texte ou sur une partie restreinte)
            * Proprotion d'Harax
                - calculer le pourcentage de mot n'ayant qu'une seule occurence

        - travail sur le nombre de faute
        - travail sur les thèmes
            (SOM)
        - travail graphique
"""


########################################################################################################################
#             Statistiques / Probabilités                                                                              #
########################################################################################################################
def frequence_mot(bag):
    """
    calcule la fréquence de chaque mot dans un sac de mot
    :param bag: <list> - liste de tous les mots d'un texte
    :return: <dict> - dictionnaire avec la fréquence par mot
    """
    freq = {}
    for mot in bag:
        if mot in freq.keys():
            freq[mot] += 1
        else:
            freq[mot] = 1

    return freq


def classement_freq(dico):
    """
    Trie un dictionnaire de mots : occurence et leur assigne un rang en fonction du nombre d'occurence
    :param dico: <dict> dictionnaire de mot: occurences
    :return: <list> {"rang": <int>, "mot": <str>, "occurences": <int>}
    """
    ranked = []
    for rang, couple in enumerate(sorted(dico.items(), key=lambda item: item[1], reverse=True), start=1):
        ranked.append({"rang": rang, "mot": couple[0], "occurences": couple[1]})

    return ranked


def freq_zipf(nb_mots, rang, s):
    """
    Retourne la fréquence théorique d'un mot selon la loi de distribution de zipf
    # help : https://iq.opengenus.org/zipfs-law/
    # help : https://www.youtube.com/watch?v=WYO8Rc4JB_Y
    # todo: développer encore
    :param nb_mots: <int> nombre d'occurence du mot le plus fréquent
    :param rang: <int> rang du mot à déterminer
    :param s: <float> environ 1
    :return: <float> nombre d'occurence estimée
    """
    h = 0
    for x in range(1, nb_mots+1):
        h += 1/(x**s)

    return 1/(rang**s) / h


########################################################################################################################
#             NLP processing                                                                                           #
########################################################################################################################
def nlp_process(texte, method):
    """
    Passe un texte à travers travers une méthode de nlp
    :param texte: <str> texte à travailler
    :param method <str> methode à utiliser pour le traitement
    :return: <list> liste de tous les mots encore présent après le traitement nlp
    """
    return


if __name__ == '__main__':
    import traitement.graphs as graphs

    ex_spam = "A POWERHOUSE GIFTING PROGRAM You Don t Want To Miss! GET IN WITH THE FOUNDERS! The MAJOR PLAYERS are " \
              "on This ONE For ONCE be where the PlayerS are This is YOUR Private Invitation EXPERTS ARE CALLING THIS" \
              " THE FASTEST WAY TO HUGE CASH FLOW EVER CONCEIVED Leverage into Over and Over Again THE QUESTION HERE" \
              " IS YOU EITHER WANT TO BE WEALTHY OR YOU DON T!!! WHICH ONE ARE YOU? I am tossing you a financial" \
              " lifeline and for your sake I Hope you GRAB onto it and hold on tight For the Ride of youR life!" \
              " Testimonials Hear what average people are doing their first few days We ve received , in day and we " \
              "are doing that over and over again! . in AL I m a single mother in FL and I ve received , in the last" \
              " days. D. S. in FL I was not sure about this when I sent off my pledge, but I got back the very next" \
              " day! . in KY I didn t have the money, so I found myself a partner to work this with. We have received" \
              " over the last days. I think I made the right decision don t you? K. C. in FL I pick up my first day" \
              " and I they gave me free leads and all the training, you can too! . in CA ANNOUNCING We will CLOSE " \
              "your sales for YOU! And Help you get a Fax Blast IMMEDIATELY Upon Your Entry!!! YOU Make the " \
              "MONEY!!! FREE LEADS!!! TRAINING!!! DON T WAIT!!! CALL NOW FAX BACK TO OR Call Name Phone Fax Email " \
              "Best Time To Call Time Zone This message is sent in compliance of the new e mail bill. Per Section , " \
              "Paragraph a C of S. , further transmissions by the sender of this email may be stopped, at no cost to" \
              " you, by sending a reply to this email address with the word REMOVE in the subject line. Errors, " \
              "omissions, and exceptions excluded. This is NOT spam! I have compiled this list from our Replicate " \
              "Database, relative to Seattle Marketing Group, The Gigt, or Turbo Team for the sole purpose of these " \
              "communications. Your continued inclusion is ONLY by your gracious permission. If you wish to not " \
              "receive this mail from me, please send an email to with Remove in the subject and you will be deleted" \
              " immediately. "

    ex_ham = "Evangelicals threat to new archbishop Direct action threat over liberal views on sexuality Stephen " \
             "Bates, religious affairs correspondent Tuesday October , The Guardian Evangelical fundamentalists last " \
             "night stepped up their campaign to oust Rowan Williams, the incoming Archbishop of Canterbury, before " \
             "he even takes up his post, by threatening to take direct action against him. The council of the Church" \
             " Society, the Church of England s oldest evangelical body, joined a younger evangelical pressure group " \
             "called Reform, which is also opposed to Dr Williams, in calling on him to recant his supposedly liberal" \
             " views on sexuality or stand down. Following an emergency meeting, the year old society, whose leaders" \
             " met the archbishop last week, proclaimed their continued opposition to his appointment and called on" \
             " all Anglicans to spurn him. The move is the latest stage of an increasingly aggressive attempt to " \
             "destabilise the new archbishop, whose leftwing political views are regarded with deep suspicion by the" \
             " conservative fringes of the evangelical movement. Some evangelicals object to Dr Williams s " \
             "acknowledgement that he has ordained a gay priest, something many bishops have done, and that those " \
             "who have sex outside marriage need not necessarily be spurned. The new archbishop has repeatedly " \
             "assured them that he respects the canons of the church. Nevertheless, the society said It is clear " \
             "that he prefers his private judgment to the voice of scripture, to the voice of tradition and to the" \
             " common mind of the church. As such he can only be a focus of disunity. The council. called upon loyal" \
             " Anglicans to pray specifically that Rowan Williams would see the error in his teaching, change his " \
             "views or stand down, it said. The society claimed to have drawn up an action plan, including calling " \
             "on bishops and primates of the million worldwide Anglican communion, of which archbishops of Canterbury" \
             " are the leaders, to distance themselves from Dr Williams s doctrinal and ethical position. It promised" \
             " it would be taking steps towards appropriate direct action . It added that Dr Williams remained on the" \
             " editorial board of a journal called Theology and Sexuality which, six months ago, published articles" \
             " allegedly commending homosexual behaviour. Despite its claim, the society does not represent the " \
             "common mind of the church. Dr Williams, currently Archbishop of Wales, was chosen by the crown " \
             "appointments commission of church members, including evangelicals, and his appointment was endorsed by" \
             " the prime minister and the Queen. He is due to succeed George Carey, who retires this month, and will " \
             "be formally enthroned at Canterbury cathedral in February. Asked what form direct action might take, " \
             "the Rev George Curry, the society s chairman, said Watch this space. Presumably it could involve a " \
             "small minority of parishes repudiating the new archbishop and seeking alternative oversight or even " \
             "demonstrations at services where Dr Williams is present. Church of England bishops, who have hitherto " \
             "largely kept their heads down during the row, are meeting next week to discuss their response to the " \
             "evangelical extremists challenge, which appears to have grown in the absence of a robust rebuttal. A " \
             "letter by senior theologians in today s Guardian, however, repudiates the evangelicals tactics, " \
             "calling them unseemly and contrary to biblical teaching. On the BBC s Thought for the Day yesterday, " \
             "Angela Tilby, vice principal of Westcott House, Cambridge, accused Dr Williams s opponents of " \
             "presumption and blackmail. It is in fact a thoroughly aggressive way to behave. It is attempting to " \
             "force an issue by emotional violence. manipulating to get your way is often preferable to painstaking " \
             "negotiation, she said. Last week, Dr Williams said he was deeply saddened. Matters of sexuality should" \
             " not have the priority or centrality that Reform and the Church Society have tried to give them. The " \
             "archbishop cannot withdraw his appointment since so many, including evangelicals, have urged him to " \
             "take the post. the archbishop believes it to be his duty under God. Yahoo! Groups Sponsor Sell a Home " \
             "with Ease! To unsubscribe from this group, send an email to Your use of Yahoo! Groups is subject to "

    fq_spam = frequence_mot(ex_spam.lower().split())
    fq_ham = frequence_mot(ex_ham.lower().split())

    sort_fqs = classement_freq(fq_spam)
    sort_fqh = classement_freq(fq_ham)
    # print(sort_fqs)
    print(sort_fqh[:3])

    s = 1.55
    print(len(ex_ham.split()))
    print(freq_zipf(len(ex_ham.split()), 1, s), end='\t')
    print(freq_zipf(len(ex_ham.split()), 2, s), end='\t')
    print(freq_zipf(len(ex_ham.split()), 3, s))

    print(len(sort_fqh))
    print(freq_zipf(len(sort_fqh), 1, s), end='\t')
    print(freq_zipf(len(sort_fqh), 2, s), end='\t')
    print(freq_zipf(len(sort_fqh), 3, s))

    graphs.show_zipf('ham', sort_fqh)
    graphs.show_zipf('spam', sort_fqs)

    exit(0)
