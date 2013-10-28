#!/usr/bin/python
# -*- coding: utf-8 -*-

import re


def remover(prog, substitution, very_big_string):
    """Take as input a string, a regex and a substitution, performs a sub on the whole string"""

    return re.sub(prog, substitution, very_big_string)


def extracter(prog, very_big_string):
    """extract from a string all occurences of a certain regex defined as input"""

    return re.findall(prog, very_big_string)


def remove_style(very_big_string):
    """take a string, extract from it all the <style> </style> and the expressions in them, return a list of styles and of expressions"""

    listOfStyles = extracter(regex_style, very_big_string)
    listOfExpressions = []
    for el in listOfStyles:
        num_of_expression = len(el.split('expression')) - 1
        st = el
        for i in range(num_of_expression):  # there is an expression
            match = re.search(regex_expressions, st)
            st = match.group(1)
            ended = False
            pos = 0
            num_par = 0
            while not ended:
                if st[pos] == '(':
                    num_par += 1
                elif st[pos] == ')':
                    num_par -= 1
                if num_par == 0:
                    ended = True
                pos += 1
            listOfExpressions.append('expression' + st[:pos])
    return (listOfStyles, listOfExpressions)


def remove_comments(very_big_string):
    """Take as input a string and return a list of html comments (<!-- .... -!>)"""

    ex = remover(regex_comment_html1, '', very_big_string)
    return extracter(regex_comment_html2, ex)


def remove_comments_hash(very_big_string):
    """Take as input a string and return a list of php comments starting with #"""

    return extracter(regex_comments_hash, very_big_string)


def remove_meta_tag(very_big_string):
    """Take as input a string and return a list of meta tags <meta .... >"""

    return extracter(regex_meta_tag, very_big_string)


def remove_empty_echo(very_big_string):
    """Take a string as input and remove all empty echoes in the form echo \"\" or echo \'\' """

    s = remover(regex_empty_echo1, '', very_big_string)
    return remover(regex_empty_echo2, '', s)


def remove_comments_php(very_big_string):
    '''Take as input a string and return all comments in c form (/*...*/ and // )'''

    l = extracter(regex_comments_php, very_big_string)
    return [el for el in l if el.startswith('/')]


def remove_whitespaces(very_big_string):
    """Take as input a string and format all multiple spaces """

    s = remover(regex_whitespaces1, ' ', very_big_string)
    s = remover(regex_whitespaces2, '\n', s)
    return remover(regex_whitespaces3, '\n', s)


def remove_empty_php_tags(very_big_string):
    s = remover(regex_empty_php_tags, '', very_big_string)
    return remover(regex_empty_php_tags2, '', s)


def remove_blanklines(very_big_string):
    s=remover(regex_blanklines,'\n', very_big_string)
    return remover(regex_whitespaces3, '\n', s)

def remove_unicode_null(very_big_string):
    return remover (regex_unicode_null, '', very_big_string)

regex_whitespaces1 = re.compile(r"[ \r\t]+")
regex_whitespaces2 = re.compile(r"[ \r]*\n[ ]*")
regex_whitespaces3 = re.compile(r"\n+")
regex_blanklines = re.compile(r"[ ]*[\r]+[ ]*")
regex_comments_php = \
    re.compile(r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"'
               , re.DOTALL | re.MULTILINE)
regex_empty_echo1 = re.compile('echo[ ]*\"[ \\\]*[ntr]*\"[ ]*[;]',
                               re.IGNORECASE)
regex_empty_echo2 = re.compile('echo[ ]*\'[ \\\]*[ntr]*\'[ ]*[;]',
                               re.IGNORECASE)
regex_meta_tag = re.compile(r'<[ \r\n\t]*meta[^>]+>', re.IGNORECASE)
regex_comments_hash = re.compile(r'\n#.*?\n')
regex_comment_html1 = re.compile(r'<![ \r\n\t]*--[^-]*?[\'\"]')
regex_comment_html2 = re.compile(r'<![ \r\n\t]*--.*?--[ \r\n\t]*>',
                                 re.DOTALL)
regex_style = re.compile(r'<[ ]*style[^<]*<[ ]*/[ ]*style[ ]*>',
                         re.DOTALL | re.IGNORECASE)
regex_expressions = re.compile('expression(.*)', re.DOTALL
                               | re.IGNORECASE)
regex_empty_php_tags=re.compile(r'<\?[ \t\n\r]*\?>', re.MULTILINE)
regex_empty_php_tags2=re.compile(r'<\?[ \t\n\r]*php[ \t\n\r]*\?>', re.MULTILINE)
regex_unicode_null = re.compile(ur'\u0000')

if __name__ == '__main__':
    import sys
    for filename in sys.argv[1:]:
        print '''

File: ''' + filename + '''

'''
        very_big_string = open(filename).read()
        print 'Before'
        print '\n' + '*' * 40
        print very_big_string
        very_big_string = remove_whitespaces(very_big_string)
        listOfComments_html = remove_comments(very_big_string)
        print 'HTML comments\n' + '-' * 20 + '\n', listOfComments_html
        for el in listOfComments_html:
            very_big_string = very_big_string.replace(el, '')

        (listOfStyles, listOfExpressions) = \
            remove_style(very_big_string)
        print 'styles:\n' + '-' * 20 + '\n', listOfStyles
        print 'expression:\n' + '-' * 20 + '\n', listOfExpressions
        for style in listOfStyles:
            very_big_string = very_big_string.replace(style, '')
        for expr in listOfExpressions:
            very_big_string = expr + ' ' + very_big_string

        listOfComments = remove_comments_hash(very_big_string)
        print 'hash comments:\n' + '-' * 20 + '\n', listOfComments
        for el in listOfComments:
            very_big_string = very_big_string.replace(el, '')

        listOfComments = remove_comments_php(very_big_string)
        print 'php comments:\n' + '-' * 20 + '\n', listOfComments
        for el in listOfComments:
            very_big_string = very_big_string.replace(el, '')

        listOfMeta = remove_meta_tag(very_big_string)
        print 'meta tags:\n' + '-' * 20 + '\n', listOfMeta
        for el in listOfMeta:
            very_big_string = very_big_string.replace(el, '')
        very_big_string = remove_empty_echo(very_big_string)
        very_big_string = remove_whitespaces(very_big_string)
        print 'After'
        print '\n' + '*' * 40
        print very_big_string
