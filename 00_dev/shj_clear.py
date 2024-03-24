#! /usr/bin/env python3
# coding: utf-8

"""
    Module de nettoyage du texte
        Nettoyage du texte
            - retrait des ponctuations
            - retrait des lignes vides et des espaces
            - retrait des retour à la ligne
            - modification liens, numeros de telephone, nombre et prix, url,
"""

# Importations
import re
from bs4 import BeautifulSoup

# metadata
__author__ = "Martial GOEHRY"
__licence__ = "GNU GPL v3"
__version__ = "0.0.0"
__status__ = "development"


def clear_html(texte):
    """ Supprime les balises des textes.
            - html
    :param texte: <str>
    :return: <str>
    """
    brut = BeautifulSoup(texte, "html.parser").text
    brut = BeautifulSoup(brut, 'html.parser').text
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
    """ Supprime les ponctualtion et les lignes vide
    :param texte: <str>
    :return: <str>
    """
    pattern_ponct = re.compile('[*#\\-_=:;<>\\[\\]"\'~)(|/$+}{@%&\\\]', flags=re.MULTILINE)
    pattern_multi_pt = re.compile('\\.+', flags=re.MULTILINE)
    pattern_nl = re.compile('^\n$', flags=re.MULTILINE)
    pattern_nl2 = re.compile('\n', flags=re.MULTILINE)
    pattern_esp = re.compile('[ \\t]+', flags=re.MULTILINE)

    temp = re.sub(pattern_ponct, ' ', texte)
    temp = re.sub(pattern_multi_pt, '.', temp)
    temp = re.sub(pattern_nl, '', temp)
    temp = re.sub(pattern_nl2, ' ', temp)
    temp = re.sub(pattern_esp, ' ', temp)
    return temp


def change_lien(texte):
    """Remplace
        - liens http(s) et ftp :    URL
        - adresses mail :           MAIL
        - numero de telephone :     TEL
    :param texte: <str>
    :return: <str>
    """
    pattern_mail = re.compile('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+')

    pattern_url1 = re.compile('(http|ftp|https)?:\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))'
                             '([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?', flags=re.MULTILINE)
    pattern_url2 = re.compile('(\\w+\\.)+\\w+', flags=re.MULTILINE)
    pattern_tel1 = re.compile('\\(\\d{3}\\)\\d+-\\d+')  # (359)1234-1000
    pattern_tel2 = re.compile('\\+\\d+([ .-]?\\d)+')    # +34 936 00 23 23

    temp = re.sub(pattern_mail, 'MAIL', texte)
    temp = re.sub(pattern_url1, 'URL', temp)
    temp = re.sub(pattern_url2, 'URL', temp)
    temp = re.sub(pattern_tel1, 'TEL', temp)
    temp = re.sub(pattern_tel2, 'TEL', temp)
    return temp


def change_nombres(texte):
    """ Remplace
        - nombre simple :       NOMBRE
        - nombre avec $|€|£ :   PRIX
    :param texte: <str>
    :return: <str>
    """
    pattern_prix1 = re.compile('[$€£]( )?\\d+([.,]\\d+)? ', flags=re.MULTILINE)
    pattern_prix2 = re.compile(' \\d+([.,]\\d+)?( )?[$€£]', flags=re.MULTILINE)
    pattern_nb = re.compile('\\d+')

    temp = re.sub(pattern_prix1, 'PRIX ', texte)
    temp = re.sub(pattern_prix2, ' PRIX ', temp)
    temp = re.sub(pattern_nb, ' NOMBRE ', temp)
    return temp


def clear_non_ascii(texte):
    """ Nettoyer les char non ascii
    :param texte: <str>
    :return: <str>
    """
    return texte.encode('ascii', 'ignore').decode()


def clear_texte(texte):
    """ Fonction principale de nettoyage du texte
    :param texte: <str>
    :return: <str>
    """
    temp = texte.lower()
    temp = clear_reply(temp)
    temp = change_lien(temp)
    temp = change_nombres(temp)
    temp = clear_ponctuation(temp)
    temp = clear_non_ascii(temp)

    return temp


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
    print(message)
    print(80*'-')
    print(clear_texte(message))
    print(80*'-')

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
    print(message_html)
    print(80*'-')
    print(clear_html(message_html))
    print(80*'-')

    message_enriched = '''
<smaller>I'd like to swap with someone also using Simple DNS to take
advantage of the trusted zone file transfer option.</smaller>
    '''
    print(message_enriched)
    print(80*'-')
    print(clear_enriched(message_enriched))
    print(80*'-')

    exit(0)
