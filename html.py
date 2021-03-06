"""Generate HTML."""

from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

IND = ' '*4  # Indentation.


def tag(name, content=None, *attributes):
    a = ''.join(' {k}="{v}"'.format(k=k, v=v) for k, v in attributes)
    if content:
        s = '<{n}{a}>{c}</{n}>'
    else:
        s = '<{n}{a} />'
    return s.format(n=name, a=a, c=content)


def href(link, content):
    return tag('a', content, ('href', link))


def ulist(items):
    s = '\n'
    for item in items:
        s += IND + tag('li', item) + '\n'
    return tag('ul', s)


def table(rows, headers=None):
    s = '\n'
    if headers:
        row = ''.join(tag('th', s) for s in headers)
        s += IND + tag('tr', row) + '\n'
    for items in rows:
        row = ''.join(tag('td', s) for s in items)
        s += IND + tag('tr', row) + '\n'
    return tag('table', s)


def head_redirect(link, time=0):
    return tag('meta', None,
               ('http-equiv', 'refresh'),
               ('content', '{t}; {l}'.format(t=time, l=link)))


def stylesheet(sheet):
    return tag('link', None,
               ('rel', 'stylesheet'),
               ('type', 'text/css'),
               ('href', sheet))


def head(title, sheet='', redirect=''):
    if sheet:
        sheet = stylesheet(sheet)
    if redirect:
        redirect = head_redirect(redirect)
    s = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" dir="ltr">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{title}</title>
{sheet}
{redirect}
</head>
<body>'''
    return s.format(title=title, sheet=sheet, redirect=redirect)


def tail():
    return '</body>\n</html>'
