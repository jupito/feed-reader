from __future__ import division, print_function

def tag(tag, s=None, params={}):
    p = ''.join([' %s="%s"' % (k, v) for k, v in params.items()])
    if s:
        return '<%s%s>%s</%s>' % (tag, p, s, tag)
    else:
        return '<%s%s />' % (tag, p)

def href(link, s):
    return tag('a', s, {'href': link})

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
    ps = {'http-equiv': 'refresh', 'content': '%s; %s' % (time, link)}
    return tag('meta', None, ps)

def stylesheet(sheet):
    ps = {'rel': 'stylesheet', 'type': 'text/css', 'href': sheet}
    return tag('link', None, ps)

def head(title, sheet=None, redirect=None):
    return '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" dir="ltr">
<head>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<title>{t}</title>
{s}
{r}
</head>
<body>'''.format(
        t=title,
        s=stylesheet(sheet) if sheet else '',
        r=head_redirect(redirect) if redirect else '',
        )

def tail():
    return '</body>\n</html>'

class Tag(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, objtype):
        return self.tag

    def tag(self, text=None, **params):
        ps = ''
        for k, v in params.items():
            ps += ' {}="{}"'.format(k, v)
        if text:
            return '<{n}{p}>{t}</{n}>'.format(n=self.name, p=ps, t=text)
        else:
            return '<{n}{p} />'.format(n=self.name, p=ps)

class Html(object):
    hr = Tag('hr')
    em = Tag('em')
    a = Tag('a')
