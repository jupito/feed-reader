from __future__ import division, print_function

IND = ' '*4 # Indentation.

def tag(name, content=None, *attributes):
    a = ''.join(' {k}="{v}"'.format(k=k, v=v) for k, v in attributes)
    d = dict(n=name, a=a, c=content)
    if content:
        content = content.encode('utf8', 'xmlcharrefreplace')
        s = '<{n}{a}>{c}</{n}>'
    else:
        s = '<{n}{a} />'
    #return s.format(**d).encode('ascii', 'xmlcharrefreplace')
    #return s.format(**d).encode('utf-8', errors='xmlcharrefreplace')
    #return unicode(s.format(**d), encoding='utf-8')
    #if content:
    #    print(type(s))
    #    print(type(content))
    #    print(content)
    #return s.format(**d).decode('utf8', errors='replace')
    return s.format(**d)

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

def head(title, sheet=None, redirect=None):
    sheet=stylesheet(sheet) if sheet else ''
    redirect=head_redirect(redirect) if redirect else ''
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
    d = dict(title=title, sheet=sheet, redirect=redirect)
    return s.format(**d)

def tail():
    return '</body>\n</html>'
