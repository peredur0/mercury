#! /usr/bin/env python3
# coding: utf-8

"""
    Module de pré-traitement du texte
        Nettoyage du texte
            - retrait des ponctuations
            - retrait des lignes vides et des espaces
            - retrait des retour à la ligne
            - modification liens, numeros de telephone, nombre et prix, url
"""

import nltk

# librairie nltk
nltk.download("words")
nltk.download("punkt")


def clear_non_ascii(texte):
    """ Nettoyer les char non ascii
    :param texte: <str> texte à traiter
    :return: <str> texte nettoyé
    """
    return texte.encode('ascii', 'ignore').decode()


def clear_non_eng(texte):
    """
    Retire les mots non anglais d'un texte
    :param texte: <str> texte à traiter
    :return: <str> texte nettoyé
    """
    words = set(nltk.corpus.words.words())
    return " ".join(mot for mot in nltk.word_tokenize(texte)
                    if mot.lower() in words or not mot.isalpha())


if __name__ == '__main__':
    txt = "Hello,This is Chinese Traditional oЧʽ    ׌ fͬһr֪ďV᣿뷽ݵI᣿    ̘IвșC᣿ һΓЎ׃ ̘I͑᣿    ԽԽ W·ֱNɠδINʽE " \
           "mailǾWϠINҲõĹߡ cVrЧߣr͡eMarketerӋ еҎģ˾ MРINӡ ֏Výwƽؑʱ^ Average Response Rate Ranges ͨ banner ads ͨż direct " \
           "mail Email һ ُIȫ ַ ÿ f HK ُIȫ f HK ُI ַ ÿ f HK   ُIȫ f HK  free download ُI ַ ÿ f HK   ُI ȫ f HK  free " \
           "download     l V lͣ ÿ f HK fl ʴ ϣ Ⱥl         һ f HK               " \
           "     һ f HK CWվL ϣ Ⱥl         һ f HK CWվL ϣ     ܛw NȺlW·lܛw HK ׌ԼһƵ ȺlW·lϵy ϵ " \
           "Ե ֵգػ݃r HK y֮ǎȫ Ӣ棬M 档׌ľWվuȫ e mailַڸ؅^ķցє ۡ  free download the sample  free download the sample ȫ򡪡 f " \
           "  y֮ǓЇσ ЧemailλַYώ죬Ը͑Ҫָĵط^,ИIeȌͶ V档 磺׌ĳ fһ֮֪ĮaƷYӍV ͶžõĽQărЂúrͣ ЧġCÿrÿ̶ȴ㣬ҲS ӵĂúֶΣеĸ֡sЄӰɣ׌I ˾̘Iý Ve mail " \
           "ͨNIܱȔMġ Mʽ ˾¾W·V꣬λЇĴW·V֮һ ҂ЌTļgˆT͸ٌIķϵy´헹،IṩѸݡЧMķա ͑Ոc YM ՈעҪķcMʽ҂؏ ۡġ ؅^ʽκ·Ҿɵy늅R 쵽 赽yk늅R English" \
           " BENIFICIARY CUSTOMER  wangjingjing A C BANK              BANK OF CHINA MIANYANG " \
           "BRANCH A C NO                 BENIFICIARY S TEL NO Čգ ˣ տyУ Їyоdꖷ    ̖ տԒ 쵽҂ṩMա " \
           "gӭŁJԃM Ԓ y֮ǾW·YӍ޹˾ ˾ַЇꑾd JԃԒ ˾ՌW·ƏV WվO W· W퓼Ĵ ׃Qg ܛwlչȣrXՃ gӭŁM "

    print(txt)
    s1 = clear_non_ascii(txt)
    print(s1)
    s2 = clear_non_eng(s1)

    print(s2)

    exit(0)
