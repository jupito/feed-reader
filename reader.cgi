#!/usr/bin/env python2

"""CGI Web UI for reading feeds."""

from __future__ import absolute_import, division, print_function
import cgi
import cgitb
cgitb.enable(display=0, logdir='cgitb', format='plain')
from operator import itemgetter
import sys

import feed_db
import html
import util

DBFILE = '_reader.db'  # Database filename.
SHEET = 'reader.css'  # Stylesheet filename.


def link_cats():
    return args.link(action='cats', cat=None, feed=None, markread=None)


def link_feeds(cat=None):
    return args.link(action='feeds', cat=cat, feed=None, markread=None)


def link_entries(cat=None, feed=None):
    return args.link(action='entries', cat=cat, feed=feed, markread=None)


def link_redirect():
    return args.link(action='redirect', markread=None)


def link_markread(ids):
    return args.link(markread=ids)


def print_top(ids=None):
    elems = [
        html.href(link_cats(), 'Categories'),
        html.href(link_feeds(), 'Feeds'),
        html.href(link_entries(), 'Entries'),
        html.href(link_redirect(), 'Redirect'),
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


def print_feedinfo(f, n_unread, n_total):
    print('<div class="feedinfo">')
    d = dict(
        id=f['id'],
        title=html.href(link_entries(feed=f['id']), f['title']),
        site=html.href(f['link'], '&rarr;'),
        feed=html.href(f['url'], '&loz;'),
        nu=n_unread, nt=n_total,
        u=util.time_fmt(f['updated']), r=util.time_fmt(f['refreshed']),
        cat=html.href(link_feeds(cat=f['category']), f['category']),
        pri=f['priority'],
        )
    rows = [
        u'{id}: {title} {site} {feed}',
        u'Category {cat}, priority {pri}',
        u'{nu} unread, {nt} total',
        u'Updated {u}, refreshed {r}',
        ]
    rows = [r.format(**d) for r in rows]
    par = html.tag('p', html.tag('br').join(rows))
    print(par)
    print('</div>')


def print_feed(f, n_unread, n_total):
    print('<div class="feed">')
    print_feedinfo(f, n_unread, n_total)
    print_description(f, plaintext=True)
    print('</div>')


def print_entryinfo(e, f):
    d = dict(updated=html.tag('em', util.time_fmt(e['updated'])),
             cat=html.href(link_entries(cat=f['category']), f['category']),
             feed=html.href(link_entries(feed=f['id']), f['title']),
             flink=html.href(f['link'], '&rarr;'))
    print('<div class="entryinfo">')
    print(u'{updated} &mdash; {cat} &mdash; {feed} {flink}'.format(**d))
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


def print_entry(e, f, cls=0):
    classes = 'entry', 'entry_alt'
    print('<div class="{}">'.format(classes[cls]))
    print_entryinfo(e, f)
    print_title(e)
    print_description(e)
    print_enclosure(e)
    print('</div>')


def show_categories(db):
    headers = ['Category', 'Feeds', 'Unread', 'Total']
    rows = [[
        html.href(link_entries(cat=cat), cat),
        html.href(link_feeds(cat=cat), db.n_feeds(cat)),
        str(db.n_entries(maxprg=0, cat=cat) or '&nbsp;&middot;&nbsp;'),
        str(db.n_entries(maxprg=1, cat=cat) or '&nbsp;&middot;&nbsp;'),
        ] for cat in db.get_categories()]
    rows.append([
        html.href(link_entries(), 'All'),
        html.href(link_feeds(), db.n_feeds()),
        str(db.n_entries(maxprg=0)),
        str(db.n_entries(maxprg=1)),
        ])
    table = html.table(rows, headers)
    print(html.head('Categories', SHEET))
    print_top()
    print('<div id="categories">')
    print(table)
    print('</div>')
    print_bottom()
    print(html.tail())


def show_feeds(db):
    feeds = db.get_feeds(args['cat'])
    feeds = sorted(feeds, key=itemgetter('priority', 'updated', 'title'))
    print(html.head('Feeds ({cat})'.format(cat=args['cat'] or 'all'), SHEET))
    print_top()
    print('<div id="feeds">')
    for f in feeds:
        n_unread = db.n_entries(maxprg=0, feed=f['id'])
        if n_unread or args['maxprg'] == 1:
            n_total = db.n_entries(maxprg=1, feed=f['id'])
            print_feed(f, n_unread, n_total)
    print('</div>')
    print_bottom()
    print(html.tail())


def show_entries(db):
    maxprg = args['maxprg']
    n = db.n_entries(maxprg=maxprg, cat=args['cat'], feed=args['feed'])
    entries = db.get_next(maxprg=maxprg, cat=args['cat'], feed=args['feed'],
                          limit=args['limit'], priority=args['priority'])
    ids = [e['id'] for e in entries]
    print(html.head('{n} in entries {p:.0%} read'.format(n=n, p=maxprg),
                    SHEET))
    print_top(ids)
    if entries:
        print('<div id="entries">')
        for i, e in enumerate(entries):
            f = db.get_feed(e['feed_id'])
            print_entry(e, f, cls=i % 2)
        print('</div>')
    else:
        rows = ['No entries left.']
        if args['cat'] or args['feed']:
            rows.append(html.href(link_entries(), 'Show all categories'))
        if args['feed']:
            f = db.get_feed(args['feed'])
            cat = f['category']
            rows.append(html.href(link_entries(cat=cat),
                                  'Show category {}'.format(cat)))
        par = html.tag('p', html.tag('br').join(rows))
        print(par)
    print_bottom(ids)
    print(html.tail())


def show_redirect(db):
    entries = db.get_next(maxprg=0, cat=args['cat'], feed=args['feed'],
                          limit=1, priority=args['priority'])
    if entries:
        e = util.sole(entries)
        print(html.head('Redirecting...', SHEET, e['link']))
        print('Redirecting to:')
        f = db.get_feed(e['feed_id'])
        print_entry(e, f)
        db.set_progress(e['id'], 1)
    else:
        print(html.head('Cannot redirect', SHEET))
        print('No unread entries.')
    print(html.tail())


def show_error(msg):
    # print(html.head('Error', sheet=SHEET))
    print(msg)
    # print(html.tail())


def main():
    util.install_utf8_conversion()
    if args['foo'] == 'baz':
        print('Content-Type: text/html')
        print()
        try:
            db = feed_db.FeedDb(DBFILE)
            for i in args['markread'] or []:
                db.set_progress(i, 1)
            action = args['action']
            if action == 'cats':
                show_categories(db)
            elif action == 'feeds':
                show_feeds(db)
            elif action == 'entries':
                show_entries(db)
            elif action == 'redirect':
                show_redirect(db)
            else:
                raise ValueError('Unknown action: {}', action)
            db.close()
        except Exception as e:
            show_error(str(e))
    else:
        cgi.test()


if __name__ == '__main__':
    args = util.CGIArgs(sys.argv[0])
    args.add_arg('foo')  # Temporary.
    args.add_arg('action', default='cats')  # What to do.
    args.add_arg('minprg', decoder=int, default=0)  # Min progress to show.
    args.add_arg('maxprg', decoder=int, default=0)  # Max progress to show.
    args.add_arg('limit', decoder=int, default=5)  # How many entries to show.
    args.add_arg('cat')  # Feed category.
    args.add_arg('feed', decoder=int)  # Feed id.
    args.add_arg('markread', decoder=util.int_tokens,
                 encoder=util.token_str)  # Entries mark read.
    args.add_arg('priority', decoder=int, default=1)  # Sort by score?
    args.parse(cgi)
    main()
