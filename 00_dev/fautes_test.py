#! /usr/bin/env python3
# coding: utf-8

import language_tool_python

tool = language_tool_python.LanguageTool('en-GB')
text = """languageTool offers spell and grammar checking. 
paste your text here and click the 'Check Text' button. the colored phrases for details on potential errors. 
use this text too see an few of of the problems that LanguageTool can detecd. do you thinks of grammar checkers? 
Please not that they are not perfect. issues get a blue marker: It's 5 P.M. in the afternoon. 
weather was nice on Thursday, 27 June 2017"""

matches = tool.check(text)
print(len(matches))

capitale = 'This sentence does not start with an uppercase letter.'
matches = [match for match in matches if not match.message == capitale]
print(len(matches))

tool.close()


def fautes_anglais(texte):
    """
    Contrôle le nombre de faute dans le texte.
    Ne prend pas en compte si la phrase ne commence par une lettre majuscule
    :param texte: <str> le texte
    :return: <int> le nombre de faute
    """
    autorise = 'This sentence does not start with an uppercase letter.'
    tool = language_tool_python.LanguageTool('en-US')
    fautes = tool.check(texte)
    fautes = [f for f in fautes if not f.message == autorise]
    tool.close()
    return len(fautes)

