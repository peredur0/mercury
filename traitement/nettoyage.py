#! /usr/bin/env python3
# coding: utf-8

"""
    Module de pré-traitement du texte
        Nettoyage du texte
            - retrait des ponctuations
            - retrait des lignes vides et des espaces
            - retrait des retours à la ligne
            - modification liens, numeros de telephone, nombre et prix, url
"""

# Importations
import re
import nltk
from bs4 import BeautifulSoup

# metadata
__author__ = "Martial GOEHRY"
__licence__ = "GNU GPL v3"
__version__ = "0.0.0"
__status__ = "development"

nltk.download("words")
nltk.download("punkt")


####################################################################################################
#             Nettoyage Initial                                                                    #
####################################################################################################
def clear_html(texte):
    """ Supprime les balises des textes.
            - html
    :param texte: <str>
    :return: <str>
    """
    brut = BeautifulSoup(texte, "lxml").text
    return brut


def clear_reply(texte):
    """ Supprime les parties correspondantes au mail precedent
    :param texte: <str>
    :return: <str>
    """
    pattern = re.compile('^>.*$', flags=re.MULTILINE)
    return re.sub(pattern, '', texte)


def clear_enriched(texte):
    """ Supprime les balises des textes enrichis
    :param texte: <str>
    :return: <str>
    """
    pattern = re.compile('<.*>')
    return re.sub(pattern, '', texte)


def clear_ponctuation(texte):
    """ Supprimer les ponctuations et les lignes vides
    :param texte: <str>
    :return: <str>
    """
    pattern_ponct = re.compile('[*#\\-_=:;<>\\[\\]"\'~)(|/$+}{@%&\\\]', flags=re.MULTILINE)
    return re.sub(pattern_ponct, '', texte)
    # Todo: tester la capture par exclusion


def clear_newline(texte):
    """
    Retire les nouvelles lignes
    :param texte: <str>
    :return: <str
    """
    pattern_nl = re.compile('^\n$', flags=re.MULTILINE)
    pattern_nl2 = re.compile('\n', flags=re.MULTILINE)
    temp = re.sub(pattern_nl, '', texte)
    temp = re.sub(pattern_nl2, ' ', temp)
    return temp


def clear_multi_space(texte):
    """
    Retire les espaces en trop
    :param texte:
    :return:
    """
    pattern_esp = re.compile('[ \\t]+', flags=re.MULTILINE)
    return re.sub(pattern_esp, ' ', texte)


def change_lien(texte, liens):
    """Sauvegarde les liens dans un dictionnaire séparé et les supprimes du texte
    :param texte: <str>
    :param liens: <dict> dictonnaire des liens
    :return: <str> - texte nettoyer
    """
    pattern_mail = re.compile('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+')

    pattern_url1 = re.compile('(http|ftp|https)?:\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))'
                             '([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?', flags=re.MULTILINE)
    pattern_url2 = re.compile('(\\w+\\.)+\\w+', flags=re.MULTILINE)
    pattern_tel1 = re.compile('\\(\\d{3}\\)\\d+-\\d+')  # (359)1234-1000
    pattern_tel2 = re.compile('\\+\\d+([ .-]?\\d)+')    # +34 936 00 23 23

    temp, liens['MAIL'] = re.subn(pattern_mail, '', texte)

    temp, liens['URL'] = re.subn(pattern_url1, '', temp)
    temp, nb = re.subn(pattern_url2, '', temp)
    liens['URL'] += nb

    temp, liens['TEL'] = re.subn(pattern_tel1, '', temp)
    temp, nb = re.subn(pattern_tel2, '', temp)
    liens['TEL'] += nb

    return temp


def change_nombres(texte, liens):
    """ Retire les données numéraire et stocke le nombre de substitution
    :param texte: <str>
    :param liens: <dict> dictonnaire des liens
    :return: <str>
    """
    monnaie = '$£€'
    pattern_prix1 = re.compile(f'[{monnaie}]( )?\\d+([.,]\\d+)? ', flags=re.MULTILINE)
    pattern_prix2 = re.compile(f' \\d+([.,]\\d+)?( )?[{monnaie}]', flags=re.MULTILINE)
    pattern_nb = re.compile('\\d+')

    temp, liens['PRIX'] = re.subn(pattern_prix1, '', texte)
    temp, nb = re.subn(pattern_prix2, '', temp)
    liens['PRIX'] += nb

    temp, liens['NOMBRE'] = re.subn(pattern_nb, '', temp)

    return temp


def clear_texte_init(texte):
    """ Fonction principale de traitement du texte
    :param texte: <str>
    :return: <str>
    """
    liens = {'URL': 0, 'MAIL': 0, 'TEL': 0, 'NOMBRE': 0, 'PRIX': 0}
    temp = clear_reply(texte)
    temp = change_lien(temp, liens)
    temp = change_nombres(temp, liens)
    temp = clear_ponctuation(temp)

    return temp, liens


####################################################################################################
#             Nettoyage Complémentaire                                                             #
####################################################################################################
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
    message = '''
Message dedicated to be a sample to show how the process is clearing the text.

Begin reply :
> He once said
>>> that it would be great
End of reply.

Substitutions :
spamassassin-talk@example.sourceforge.net
https://www.inphonic.com/r.asp?r=sourceforge1&refcode1=vs3390
hello.foo.bar
between $ 25 and 25,21 $

A number is : 2588,8 588
Phone type a : (359)1234-1000
Phone type b : +34 936 00 23 23
Ponctuation : ----## ..
~ ~~~~~
    '''
    text, liens = clear_texte_init(message)
    print(liens)
    print(text)

    message_html = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <title>Foobar</title>
</head>
<body>
I actually thought of this kind of active chat at AOL 
bringing up ads based on what was being discussed and 
other features
  <pre wrap="">On 10/2/02 12:00 PM, "Mr. FoRK" 
  <a class="moz-txt-link-rfc2396E"href="mailto:fork_
  list@hotmail.com">&lt;fork_list@hotmail.com&gt;</a> 
  wrote: Hello There, General Kenobi !?
<br>
</body>
</html>
    '''
    print(clear_html(message_html))
    print(80*'-')

    message_enriched = '''
<smaller>I'd like to swap with someone also using Simple DNS to take
advantage of the trusted zone file transfer option.</smaller>
    '''
    print(clear_enriched(message_enriched))
    print(80*'-')

    exit(0)
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
