#!/usr/bin/env python2

from __future__ import division, print_function
import cgi
import cgitb; cgitb.enable()
import codecs
import sys

import feed_db
import html
import util

DB_FILENAME = '_reader.db' # Database filename.
CONTENT_TYPE = 'Content-Type: text/html\n'
SHEET = 'reader.css'
DEFAULT_LIMIT = 5 # How many articles to show simultaneously.

def get_args():
    """Collect arguments into a dictionary."""
    form = cgi.FieldStorage()
    arg_names = ['foo', 'action', 'any', 'limit', 'cat', 'feed', 'markread']
    args = {x: form.getvalue(x) or '' for x in arg_names}
    if args['limit'] and args['limit'].isdigit():
        args['limit'] = int(args['limit'])
    else:
        args['limit'] = DEFAULT_LIMIT
    return args

def markread(db):
    for i in args['markread'].split(','):
        if i.isdigit():
            db.set_progress(int(i), 1)
    args['markread'] = ''

def link(a):
    url = sys.argv[0]
    params = []
    for k, v in a.iteritems():
        if v:
            params.append('{k}={v}'.format(k=k, v=v))
    return url + '?' + '&'.join(params)

def link_cats():
    a = args.copy()
    a['action'] = 'cats'
    a['cat'] = ''
    a['feed'] = ''
    return link(a)

def link_feeds(cat=None):
    a = args.copy()
    a['action'] = 'feeds'
    if cat != None:
        a['cat'] = cat
    a['feed'] = ''
    return link(a)

def link_entries(cat=None, feed=None):
    a = args.copy()
    a['action'] = 'entries'
    if cat != None:
        a['cat'] = cat
    if feed != None:
        a['feed'] = feed
    return link(a)

def link_redirect():
    a = args.copy()
    a['action'] = 'redirect'
    return link(a)

def link_markread(ids):
    a = args.copy()
    a['markread'] = ','.join(map(str, ids))
    return link(a)

def print_top(ids=None):
    elems = [
            html.href(link_cats(), 'Categories'),
            html.href(link_feeds(), 'Feeds'),
            html.href(link_entries(), 'Entries'),
            html.href(link_redirect(), 'Redirect'),
            str(util.file_age(DB_FILENAME)),
            ]
    if ids:
        elems.append(html.href(link_markread(ids), 'Mark these read'))
    print('<div id="top">')
    print(' | '.join(elems))
    print('</div>')

def print_bottom(ids=None):
    print('<div id="bottom">')
    if ids:
        print(html.href(link_markread(ids), 'Mark these read'))
    print('</div>')

def show_categories(db):
    print(html.head('Categories', SHEET))
    print_top()
    headers = ['Category', 'Feeds', 'Unread', 'Total']
    rows = [[
            html.href(link_entries(cat), cat),
            html.href(link_feeds(cat), db.n_feeds(cat)),
            str(db.n_entries(maxprg=0, cat=cat)),
            str(db.n_entries(maxprg=1, cat=cat)),
            ] for cat in db.get_categories()]
    rows.append([
            html.href(link_entries(''), 'All'),
            html.href(link_feeds(''), db.n_feeds()),
            str(db.n_entries(maxprg=0)),
            str(db.n_entries(maxprg=1)),
            ])
    table = html.table(rows, headers)
    print('<div id="categories">')
    print(table)
    print('</div>')
    print_bottom()
    print(html.tail())

def print_feed_(f, n_unread, n_total):
    feed = html.href(link_entries('', f['id']), f['title'])
    link = html.href(f['link'], '=>')
    cat = html.href(link_feeds(f['category']), f['category'])
    priority = 'Priority %i' % f['priority']
    n_entries = '%i unread, %i total' % (n_unread, n_total)
    updated = 'Updated %s' % util.time_fmt(f['updated'])
    refreshed = 'Refreshed %s' % util.time_fmt(f['refreshed'])
    desc = f['description'] or ''
    rows = [feed + link, cat, priority, n_entries, updated, refreshed, desc]
    par = html.tag('p', html.tag('br').join(rows))
    print('<div class="feed">')
    print(par)
    print('</div>')

def print_feedinfo(f, n_unread, n_total):
    print('<div class="feedinfo">')
    rows = [
            '%i: %s %s %s' % (
                    f['id'],
                    html.href(link_entries('', f['id']), f['title']),
                    html.href(f['link'], '(site)'),
                    html.href(f['url'], '(feed)'),
                    ),
            'Category %s, priority %i' % (
                    html.href(link_feeds(f['category']), f['category']),
                    f['priority']),
            '%i unread, %i total' % (n_unread, n_total),
            ]
    par = html.tag('p', html.tag('br').join(rows))
    print(par)
    print('</div>')

def print_feeddates(f):
    print('<div class="feeddates">')
    d = dict(u=util.time_fmt(f['updated']), r=util.time_fmt(f['refreshed']))
    print('Updated {u}, refreshed {r}'.format(**d))
    print('</div>')

def print_feed(f, n_unread, n_total):
    print('<div class="feed">')
    print_feedinfo(f, n_unread, n_total)
    print_feeddates(f)
    print_description(f, plaintext=True)
    print('</div>')

def show_feeds(db):
    feeds = db.get_feeds(args['cat'])
    print(html.head('Feeds ({cat})'.format(cat=args['cat'] or 'all'), SHEET))
    print_top()
    print('<div id="feeds">')
    for f in feeds:
        n_unread = db.n_entries(maxprg=0, feed=f['id'])
        n_total = db.n_entries(maxprg=1, feed=f['id'])
        print_feed(f, n_unread, n_total)
    print('</div>')
    print_bottom()
    print(html.tail())

def print_entryinfo(e, f):
    updated = html.tag('em', util.time_fmt(e['updated']))
    cat = html.href(link_entries(f['category'], ''), f['category'])
    feed = html.href(link_entries('', f['id']), f['title'])
    flink = html.href(f['link'], '=>')
    print('<div class="entryinfo">')
    print(' &mdash; '.join([updated, cat, feed + flink]))
    print('</div>')

def print_title(x):
    print('<div class="title">')
    print(html.href(x['link'], x['title']))
    print('</div>')

def print_description(x, plaintext=False):
    desc = x['description']
    if desc:
        if plaintext:
            desc = util.HTMLStripper.strip(desc)
        print('<div class="description">')
        print(desc)
        print('</div>')

def print_enclosure(e):
    url = e['enc_url']
    if url:
        d = dict(t=e['enc_type'] or 'unknown', l=e['enc_length'] or 'unknown')
        print('<div class="enclosure">')
        print(html.href(url, 'Enclosure (type: {t}, length: {l})'.format(**d)))
        print('</div>')

def print_entry(e, f, alt=False):
    print('<div class="%s">' % ('entry_alt' if alt else 'entry'))
    print_entryinfo(e, f)
    print_title(e)
    print_description(e)
    print_enclosure(e)
    print('</div>')

def show_entries(db):
    any = args['any']
    n = db.n_entries(maxprg=any, cat=args['cat'], feed=args['feed'])
    entries = db.get_next(maxprg=any, cat=args['cat'], feed=args['feed'],
            limit=args['limit'])
    ids = [e['id'] for e in entries]
    print(html.head('%i in %s entries' % (n, 'all' if any else 'unread'), SHEET))
    print_top(ids)
    print('<div id="entries">')
    for i, e in enumerate(entries):
        f = db.get_feed(e['feed_id'])
        print_entry(e, f, i%2)
    print('</div>')
    print_bottom(ids)
    print(html.tail())

def redirect(db):
    entries = db.get_next(maxprg=0, cat=args['cat'], feed=args['feed'], limit=1)
    if entries:
        e = entries[0]
        print(html.head('Redirecting...', SHEET, e['link']))
        print('Redirecting to:')
        f = db.get_feed(e['feed_id'])
        print_entry(e, f)
        db.set_progress(e['id'], 1)
    else:
        print(html.head('Cannot redirect', SHEET))
        print('No unread entries.')
    print(html.tail())

def reader():
    db = feed_db.FeedDb(DB_FILENAME)
    markread(db)
    action = args['action'] or 'cats'
    if action == 'cats':
        show_categories(db)
    elif action == 'feeds':
        show_feeds(db)
    elif action == 'entries':
        show_entries(db)
    elif action == 'redirect':
        redirect(db)
    db.close()


# Install UTF-8 conversion wrapper for output.
if sys.stdout.encoding != 'UTF-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')
if sys.stderr.encoding != 'UTF-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr, 'strict')

args = get_args()
print(CONTENT_TYPE)
if args['foo'] == 'baz':
    try:
        reader()
    except Exception, e:
        if e.message == 'database is locked':
            print(e.message)
        else:
            raise
else:
    print(sys.path)
    cgi.test()
