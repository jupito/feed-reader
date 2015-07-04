from __future__ import division, print_function
import collections

def tag(name, content=None, attributes={}):
    a = ''.join(' {k}="{v}"'.format(k=k, v=v) for k, v in attributes.items())
    d = dict(n=name, a=a, c=content)
    if content:
        s = '<{n}{a}>{c}</{n}>'
    else:
        s = '<{n}{a} />'
    return s.format(**d)

def href(link, content):
    return tag('a', content, {'href': link})

def list(items):
    s = '\n'
    for item in items:
        s += ' ' * 4 + tag('li', item) + '\n'
    return tag('ul', s)

def table(rows, headers=None):
    s = '\n'
    if headers:
        row = reduce(lambda x, y: x + tag('th', y), headers, '')
        s += ' ' * 4 + tag('tr', row) + '\n'
    for items in rows:
        row = reduce(lambda x, y: x + tag('td', y), items, '')
        s += ' ' * 4 + tag('tr', row) + '\n'
    return tag('table', s)

def head_redirect(link, time=0):
    attributes = collections.OrderedDict([
            ('http-equiv', 'refresh'),
            ('content', '{t}; {l}'.format(t=time, l=link)),
            ])
    return tag('meta', None, attributes=attributes)

def stylesheet(sheet):
    attributes = collections.OrderedDict([
            ('rel', 'stylesheet'),
            ('type', 'text/css'),
            ('href', sheet),
            ])
    return tag('link', None, attributes=attributes)

def head(title, sheet=None, redirect=None):
    s = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" dir="ltr">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{t}</title>
{s}
{r}
</head>
<body>'''
    d = dict(t=title,
        s=stylesheet(sheet) if sheet else '',
        r=head_redirect(redirect) if redirect else '')
    return s.format(**d)

def tail():
    return '</body>\n</html>'
